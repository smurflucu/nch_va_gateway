import { Link } from 'react-router-dom'
import { ROUTES } from '@/config/routes'
import { APP_NAME } from '@/config/constants'
import { useAuthStore } from '@/features/auth'
import Button from '@/components/ui/Button'

export default function HomePage() {
  const user = useAuthStore((s) => s.user)
  return (
    <div>
      <h1 style={{ marginBottom: 12 }}>
        <span style={{ color: '#25D366' }}>●</span> {APP_NAME}
      </h1>
      <p style={{ color: 'var(--text-dim)', maxWidth: 560, lineHeight: 1.6 }}>
        Platform WhatsApp gateway (unofficial) multi-nomor: kirim & broadcast pesan,
        auto-reply berdasarkan kata kunci, inbox, jadwal terjadwal, dan API untuk aplikasi lain.
      </p>
      <div style={{ marginTop: 20 }}>
        {user
          ? <Link to={ROUTES.sessions}><Button>Buka Dashboard</Button></Link>
          : <Link to={ROUTES.login}><Button>Masuk untuk mulai</Button></Link>}
      </div>
      <p style={{ color: 'var(--text-dim)', fontSize: 13, marginTop: 24, maxWidth: 560 }}>
        ⚠️ Catatan: penggunaan WhatsApp non-resmi melanggar ToS WhatsApp dan nomor berisiko
        diblokir bila mengirim terlalu agresif. Gunakan jeda antar pesan & hormati opt-out.
      </p>
    </div>
  )
}
