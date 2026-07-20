/**
 * WA Gateway — engine WhatsApp non-resmi (Baileys), multi-session.
 *
 * Tugasnya SEMPIT dan disengaja: cuma pegang koneksi WhatsApp.
 *   - start / stop session (per nomor WA)
 *   - kasih QR untuk login
 *   - kirim pesan
 *   - forward event (qr / connected / disconnected / pesan masuk) ke backend FastAPI via webhook
 *
 * Semua "otak" (auth user, kontak, template, jadwal, log) ada di FastAPI.
 * Endpoint di sini diproteksi header X-Internal-Token — TIDAK boleh diekspos ke publik.
 */
import express from 'express'
import qrcode from 'qrcode'
import pino from 'pino'
import { Boom } from '@hapi/boom'
import fs from 'fs'
import path from 'path'
import {
  default as makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} from '@whiskeysockets/baileys'

const PORT = process.env.PORT || 3001
const AUTH_DIR = process.env.AUTH_DIR || './auth'
const INTERNAL_TOKEN = process.env.WA_INTERNAL_TOKEN || 'change-me-internal-token'
const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://backend:8000/api/v1/wa/webhook'
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'change-me-webhook-secret'

const logger = pino({ level: process.env.LOG_LEVEL || 'info' })
fs.mkdirSync(AUTH_DIR, { recursive: true })

/** Map sessionKey -> { sock, status, qr, phone } */
const sessions = new Map()

/** Normalisasi nomor ke JID WhatsApp. 08xx -> 628xx. */
function toJid(number) {
  if (number.includes('@')) return number
  let n = String(number).replace(/[^0-9]/g, '')
  if (n.startsWith('0')) n = '62' + n.slice(1)
  return `${n}@s.whatsapp.net`
}

/**
 * Kembalikan NOMOR (user saja) dari sebuah message key.
 * Kalau remoteJid berupa LID (@lid), pakai senderPn kalau ada, atau resolve
 * lewat lidMapping. getPNForLID mengembalikan JID ber-device (`628..:0@...`),
 * jadi buang bagian device (`:0`) dan domain (`@...`) supaya nomor bersih.
 */
async function resolvePn(sock, key) {
  const jid = key.remoteJid || ''
  let pnJid = jid
  if (jid.endsWith('@lid')) {
    pnJid = key.senderPn || null
    if (!pnJid) {
      try {
        pnJid = await sock.signalRepository?.lidMapping?.getPNForLID?.(jid)
      } catch (_) {}
    }
    pnJid = pnJid || jid
  }
  // ambil user saja: buang device (":0") dan domain ("@...")
  return pnJid.split('@')[0].split(':')[0]
}

async function postWebhook(sessionKey, event, data) {
  try {
    await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Webhook-Secret': WEBHOOK_SECRET },
      body: JSON.stringify({ sessionKey, event, data }),
    })
  } catch (e) {
    logger.warn({ err: e.message, sessionKey, event }, 'gagal kirim webhook ke backend')
  }
}

async function startSession(sessionKey) {
  if (sessions.get(sessionKey)?.status === 'connecting' || sessions.get(sessionKey)?.status === 'connected') {
    return sessions.get(sessionKey)
  }

  const folder = path.join(AUTH_DIR, sessionKey)
  const { state, saveCreds } = await useMultiFileAuthState(folder)
  const { version } = await fetchLatestBaileysVersion()

  /**
   * Cache pesan terkirim/diterima (key `${jid}:${id}` -> proto message content).
   * WAJIB: waktu HP penerima gagal dekripsi, dia minta retry — Baileys panggil
   * getMessage() untuk enkripsi ulang. Tanpa ini penerima stuck di
   * "Waiting for this message. This may take a while."
   */
  const msgStore = new Map()
  const rememberMessage = (key, message) => {
    if (!key?.id || !message) return
    // Kunci HANYA pakai key.id — ID pesan unik global. Kalau dikunci pakai
    // remoteJid, retry gagal: waktu kirim remoteJid = PN (@s.whatsapp.net),
    // tapi waktu retry penerima pakai LID (@lid) → lookup meleset → penerima
    // stuck "Waiting for this message".
    msgStore.set(key.id, message)
    // batasi memori — buang yang paling lama kalau sudah > 1000
    if (msgStore.size > 1000) msgStore.delete(msgStore.keys().next().value)
  }

  const sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,
    logger: pino({ level: process.env.WA_LOG_LEVEL || 'silent' }),
    browser: ['Nch WA Gateway', 'Chrome', '1.0.0'],
    getMessage: async (key) => msgStore.get(key.id) || undefined,
  })

  const entry = { sock, status: 'connecting', qr: null, phone: null, rememberMessage }
  sessions.set(sessionKey, entry)

  sock.ev.on('creds.update', saveCreds)

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update

    if (qr) {
      entry.qr = await qrcode.toDataURL(qr)
      entry.status = 'qr'
      postWebhook(sessionKey, 'qr', { qr: entry.qr })
    }

    if (connection === 'open') {
      entry.status = 'connected'
      entry.qr = null
      entry.phone = sock.user?.id?.split(':')[0] || null
      logger.info({ sessionKey, phone: entry.phone }, 'session connected')
      postWebhook(sessionKey, 'connected', { phone: entry.phone })
    }

    if (connection === 'close') {
      const statusCode = new Boom(lastDisconnect?.error)?.output?.statusCode
      const loggedOut = statusCode === DisconnectReason.loggedOut
      entry.status = loggedOut ? 'logged_out' : 'disconnected'
      logger.warn({ sessionKey, statusCode, loggedOut }, 'session closed')
      postWebhook(sessionKey, 'disconnected', { reason: statusCode, loggedOut })

      if (loggedOut) {
        // Sesi ditutup dari HP → hapus kredensial, harus scan ulang
        fs.rmSync(folder, { recursive: true, force: true })
        sessions.delete(sessionKey)
      } else {
        // Koneksi putus sementara → reconnect otomatis
        setTimeout(() => startSession(sessionKey).catch((e) => logger.error(e)), 3000)
      }
    }
  })

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    // Simpan SEMUA pesan (termasuk fromMe) supaya retry-request bisa dilayani
    for (const m of messages) rememberMessage(m.key, m.message)
    if (type !== 'notify') return
    for (const m of messages) {
      if (!m.message) continue
      const text =
        m.message.conversation ||
        m.message.extendedTextMessage?.text ||
        m.message.imageMessage?.caption ||
        m.message.videoMessage?.caption ||
        ''
      const jid = m.key.remoteJid || ''
      // Abaikan pesan grup & status broadcast untuk MVP
      if (jid.endsWith('@g.us') || jid === 'status@broadcast') continue
      // WA baru pakai LID (@lid) yang menyembunyikan nomor asli. key.senderPn
      // sering kosong di upsert, jadi resolve lewat lidMapping → nomor asli.
      const from = await resolvePn(sock, m.key)
      postWebhook(sessionKey, 'message', {
        from,
        fromMe: !!m.key.fromMe,
        id: m.key.id,
        text,
        timestamp: Number(m.messageTimestamp) || Math.floor(Date.now() / 1000),
        pushName: m.pushName || '',
      })
    }
  })

  return entry
}

// ---- HTTP API (internal, dipanggil FastAPI) ----
const app = express()
app.use(express.json({ limit: '2mb' }))

app.use((req, res, next) => {
  if (req.headers['x-internal-token'] !== INTERNAL_TOKEN) {
    return res.status(401).json({ detail: 'unauthorized' })
  }
  next()
})

app.get('/health', (_req, res) => res.json({ ok: true, sessions: sessions.size }))

app.post('/sessions', async (req, res) => {
  const { sessionKey } = req.body
  if (!sessionKey) return res.status(400).json({ detail: 'sessionKey wajib' })
  try {
    const entry = await startSession(sessionKey)
    res.json({ sessionKey, status: entry.status })
  } catch (e) {
    logger.error(e)
    res.status(500).json({ detail: e.message })
  }
})

app.get('/sessions/:key', (req, res) => {
  const entry = sessions.get(req.params.key)
  if (!entry) return res.json({ status: 'disconnected', qr: null, phone: null })
  res.json({ status: entry.status, qr: entry.qr, phone: entry.phone })
})

app.post('/sessions/:key/send', async (req, res) => {
  const entry = sessions.get(req.params.key)
  if (!entry || entry.status !== 'connected') {
    return res.status(409).json({ detail: 'session belum terhubung' })
  }
  const { to, text } = req.body
  if (!to || !text) return res.status(400).json({ detail: 'to & text wajib' })
  try {
    const jid = toJid(to)
    const sent = await entry.sock.sendMessage(jid, { text })
    if (sent?.key && sent?.message) entry.rememberMessage(sent.key, sent.message)
    logger.info({ to: jid, sentKey: sent?.key }, 'send-result')
    res.json({ id: sent?.key?.id || null })
  } catch (e) {
    logger.error(e)
    res.status(500).json({ detail: e.message })
  }
})

app.delete('/sessions/:key', async (req, res) => {
  const key = req.params.key
  const entry = sessions.get(key)
  try {
    await entry?.sock?.logout().catch(() => {})
  } catch (_) {}
  fs.rmSync(path.join(AUTH_DIR, key), { recursive: true, force: true })
  sessions.delete(key)
  res.json({ ok: true })
})

// Restore semua session yang kredensialnya masih tersimpan waktu startup
function restoreSessions() {
  if (!fs.existsSync(AUTH_DIR)) return
  for (const dir of fs.readdirSync(AUTH_DIR)) {
    if (fs.statSync(path.join(AUTH_DIR, dir)).isDirectory()) {
      startSession(dir).catch((e) => logger.error({ err: e.message, dir }, 'gagal restore session'))
    }
  }
}

app.listen(PORT, () => {
  logger.info(`WA gateway listening on :${PORT}`)
  restoreSessions()
})
