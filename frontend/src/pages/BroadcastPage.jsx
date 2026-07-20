import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Textarea from '@/components/ui/Textarea'
import Badge from '@/components/ui/Badge'
import { useAuthStore } from '@/features/auth'
import { useSessions, useContacts, useBroadcasts, usePendingBroadcasts, waApi } from '@/features/wa'

export default function BroadcastPage() {
  const me = useAuthStore((s) => s.user)
  const isRegular = me.role === 'user'
  const canApprove = me.role === 'admin' || me.role === 'supervisor'

  const { items: sessions } = useSessions()
  const { items: contacts } = useContacts()
  const { items: broadcasts, refresh } = useBroadcasts()
  const { items: pending, refresh: refreshPending } = usePendingBroadcasts(canApprove ? undefined : null)

  const [name, setName] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [body, setBody] = useState('')
  const [manual, setManual] = useState('')
  const [picked, setPicked] = useState({})
  const [delay, setDelay] = useState(5)
  const [schedule, setSchedule] = useState('')
  const [msg, setMsg] = useState(null)
  const [busy, setBusy] = useState(false)

  const connected = sessions.filter((s) => s.status === 'connected')

  const buildTargets = () => {
    const t = []
    contacts.forEach((c) => { if (picked[c.id]) t.push({ phone: c.phone, name: c.name }) })
    manual.split(/[\n,]/).map((x) => x.trim()).filter(Boolean).forEach((p) => t.push({ phone: p, name: '' }))
    return t
  }

  const submit = async () => {
    const targets = buildTargets()
    if (!targets.length) { setMsg({ ok: false, text: 'Pilih minimal 1 tujuan' }); return }
    setBusy(true); setMsg(null)
    try {
      await waApi.createBroadcast({
        name, session_id: Number(sessionId), body, targets,
        delay_seconds: Number(delay),
        scheduled_at: schedule ? new Date(schedule).toISOString() : null,
      })
      setMsg({
        ok: true,
        text: isRegular ? 'Broadcast dikirim untuk approval supervisor ⏳'
          : schedule ? 'Broadcast dijadwalkan ✅' : 'Broadcast dimulai ✅',
      })
      setName(''); setBody(''); setManual(''); setPicked({}); setSchedule('')
      refresh(); if (canApprove) refreshPending()
    } catch (e) {
      setMsg({ ok: false, text: e.response?.data?.detail || 'Gagal' })
    } finally {
      setBusy(false)
    }
  }

  const act = async (b, kind) => {
    if (kind === 'reject' && !confirm(`Tolak broadcast "${b.name}"?`)) return
    await (kind === 'approve' ? waApi.approveBroadcast(b.id) : waApi.rejectBroadcast(b.id))
    refreshPending(); refresh()
  }

  const targetCount = Object.values(picked).filter(Boolean).length +
    manual.split(/[\n,]/).map((x) => x.trim()).filter(Boolean).length

  return (
    <div>
      <div className="page-head">
        <h1>Broadcast / Blast</h1>
        <p>
          Beri jeda antar pesan (anti-banned). Pakai <code>{'{{name}}'}</code> untuk personalisasi.
          {isRegular && ' Broadcast Anda perlu disetujui supervisor sebelum dikirim.'}
        </p>
      </div>

      {/* Antrian approval — supervisor/admin */}
      {canApprove && pending.length > 0 && (
        <Card style={{ marginBottom: 18, borderColor: 'var(--warn)', background: 'var(--warn-soft)' }}>
          <h3 style={{ marginBottom: 12 }}>⏳ Menunggu approval ({pending.length})</h3>
          {pending.map((b) => (
            <div key={b.id} className="list-item" style={{ borderColor: 'rgba(0,0,0,.06)' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{b.name}</div>
                <div className="muted" style={{ fontSize: 13 }}>{b.total} tujuan · oleh user #{b.user_id}</div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button variant="success" size="sm" onClick={() => act(b, 'approve')}>Setujui</Button>
                <Button variant="ghost" size="sm" onClick={() => act(b, 'reject')}>Tolak</Button>
              </div>
            </div>
          ))}
        </Card>
      )}

      <Card style={{ marginBottom: 18 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Input label="Nama kampanye" value={name} onChange={(e) => setName(e.target.value)} />
          <Select label="Dari nomor" value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
            <option value="">— pilih nomor —</option>
            {connected.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.phone})</option>)}
          </Select>
        </div>

        <Textarea label="Isi pesan" value={body} onChange={(e) => setBody(e.target.value)}
                  placeholder="Halo {{name}}, ada info penting…" />

        {contacts.length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <span style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-dim)', marginBottom: 6 }}>
              Pilih dari kontak
            </span>
            <div style={{ maxHeight: 160, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 10, padding: 10 }}>
              {contacts.map((c) => (
                <label key={c.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '4px 0', fontSize: 14 }}>
                  <input type="checkbox" checked={!!picked[c.id]}
                         onChange={(e) => setPicked({ ...picked, [c.id]: e.target.checked })} />
                  {c.name || '(tanpa nama)'} — {c.phone}
                </label>
              ))}
            </div>
          </div>
        )}

        <Textarea label="Atau tempel nomor manual (1 per baris / pisah koma)" rows={3}
                  value={manual} onChange={(e) => setManual(e.target.value)} placeholder="081111&#10;082222" />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Input label="Jeda antar pesan (detik)" type="number" min={0} max={120}
                 value={delay} onChange={(e) => setDelay(e.target.value)} />
          <Input label="Jadwalkan (opsional)" type="datetime-local"
                 value={schedule} onChange={(e) => setSchedule(e.target.value)} />
        </div>

        <Button onClick={submit} disabled={busy || !sessionId || !body || !name || !targetCount}>
          {busy ? 'Memproses…'
            : isRegular ? `Ajukan ke ${targetCount} nomor (perlu approval)`
            : `${schedule ? 'Jadwalkan' : 'Kirim'} ke ${targetCount} nomor`}
        </Button>
        {msg && <p style={{ marginTop: 12, color: msg.ok ? 'var(--success)' : 'var(--danger)' }}>{msg.text}</p>}
      </Card>

      <h2 style={{ marginBottom: 10 }}>Riwayat</h2>
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        {!broadcasts.length && <p className="muted" style={{ padding: 20 }}>Belum ada broadcast.</p>}
        {broadcasts.map((b) => (
          <div key={b.id} className="list-item" style={{ padding: '13px 20px' }}>
            <div>
              <div style={{ fontWeight: 600 }}>{b.name}</div>
              <div className="muted" style={{ fontSize: 13 }}>
                {b.sent}/{b.total} terkirim{b.failed ? ` · ${b.failed} gagal` : ''}
                {b.scheduled_at ? ` · dijadwalkan ${new Date(b.scheduled_at).toLocaleString('id-ID')}` : ''}
              </div>
            </div>
            <Badge>{b.status}</Badge>
          </div>
        ))}
      </Card>
    </div>
  )
}
