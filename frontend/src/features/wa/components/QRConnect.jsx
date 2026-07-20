import { useEffect, useState } from 'react'
import { waApi } from '../services/wa.api'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'

/** Modal untuk scan QR. Polling status tiap 2 detik sampai connected. */
export default function QRConnect({ session, onClose }) {
  const [status, setStatus] = useState(session.status)
  const [qr, setQr] = useState('')

  useEffect(() => {
    let alive = true
    const tick = async () => {
      try {
        const { data } = await waApi.sessionStatus(session.id)
        if (!alive) return
        setStatus(data.status)
        setQr(data.qr || '')
      } catch (_) {}
    }
    tick()
    const t = setInterval(tick, 2000)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [session.id])

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,.6)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12,
          padding: 28, width: 360, textAlign: 'center',
        }}
      >
        <h3 style={{ marginBottom: 6 }}>{session.name}</h3>
        <div style={{ marginBottom: 16 }}><Badge>{status}</Badge></div>

        {status === 'connected' ? (
          <p style={{ color: '#2ecc71', margin: '24px 0' }}>
            ✅ Terhubung{session.phone ? ` · ${session.phone}` : ''}
          </p>
        ) : qr ? (
          <>
            <img src={qr} alt="QR" style={{ width: 260, height: 260, background: '#fff', borderRadius: 8 }} />
            <p style={{ color: 'var(--text-dim)', fontSize: 13, marginTop: 12 }}>
              Buka WhatsApp → Perangkat Tertaut → Tautkan Perangkat, lalu scan.
            </p>
          </>
        ) : (
          <p style={{ color: 'var(--text-dim)', margin: '40px 0' }}>Menyiapkan QR…</p>
        )}

        <div style={{ marginTop: 16, display: 'flex', gap: 8, justifyContent: 'center' }}>
          <Button variant="ghost" onClick={onClose}>Tutup</Button>
        </div>
      </div>
    </div>
  )
}
