import { Link } from 'react-router-dom'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { ROUTES } from '@/config/routes'
import { useAuthStore } from '@/features/auth'
import { useSessions, useInbox, useBroadcasts } from '@/features/wa'

function StatCard({ icon, tone, label, value, sub, to }) {
  const body = (
    <Card className={to ? 'card-link' : ''} style={{ padding: 18 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <div className="avatar" style={{ width: 30, height: 30, background: `var(--${tone}-soft)`, color: `var(--${tone})`, fontSize: 15 }}>{icon}</div>
        <span style={{ fontSize: 13, color: 'var(--text-dim)', fontWeight: 500 }}>{label}</span>
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.02em' }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>{sub}</div>}
    </Card>
  )
  return to ? <Link to={to}>{body}</Link> : body
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const { items: sessions } = useSessions()
  const { items: messages } = useInbox()
  const { items: broadcasts } = useBroadcasts()

  const connected = sessions.filter((s) => s.status === 'connected').length
  const incoming = messages.filter((m) => m.direction === 'in').length
  const outgoing = messages.filter((m) => m.direction === 'out').length
  const activeBc = broadcasts.filter((b) => ['running', 'scheduled', 'pending_approval'].includes(b.status)).length
  const recent = [...messages].slice(0, 6)

  const hour = new Date().getHours()
  const greet = hour < 11 ? 'Selamat pagi' : hour < 15 ? 'Selamat siang' : hour < 18 ? 'Selamat sore' : 'Selamat malam'

  return (
    <div>
      <div className="page-head">
        <div className="muted" style={{ fontSize: 13 }}>{greet}, {user.full_name || user.email}</div>
        <h1>Ringkasan aktivitas Anda</h1>
      </div>

      <div className="grid-stats" style={{ marginBottom: 18 }}>
        <StatCard icon="✆" tone="success" label="Nomor terhubung" value={`${connected}/${sessions.length}`} sub="perangkat aktif" to={ROUTES.sessions} />
        <StatCard icon="✉" tone="accent" label="Pesan masuk" value={incoming} sub="di scope Anda" to={ROUTES.inbox} />
        <StatCard icon="➤" tone="accent" label="Pesan keluar" value={outgoing} sub="terkirim" to={ROUTES.inbox} />
        <StatCard icon="📣" tone="warn" label="Broadcast aktif" value={activeBc} sub="berjalan / menunggu" to={ROUTES.broadcast} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.3fr) minmax(0,1fr)', gap: 18, alignItems: 'start' }}>
        {/* Status nomor */}
        <Card>
          <div className="row-between" style={{ marginBottom: 8 }}>
            <h3>Status nomor</h3>
            <Link to={ROUTES.sessions} style={{ fontSize: 13 }}>Lihat semua →</Link>
          </div>
          {!sessions.length && <p className="muted">Belum ada nomor dialokasikan untuk tim Anda.</p>}
          {sessions.map((s) => (
            <div key={s.id} className="list-item">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div className="avatar" style={{ background: 'var(--success-soft)', color: 'var(--success)' }}>✆</div>
                <div>
                  <div style={{ fontWeight: 600 }}>{s.name}</div>
                  <div className="muted" style={{ fontSize: 13 }}>{s.phone || 'belum tertaut'}</div>
                </div>
              </div>
              <Badge>{s.status}</Badge>
            </div>
          ))}
        </Card>

        {/* Aktivitas terkini */}
        <Card>
          <div className="row-between" style={{ marginBottom: 8 }}>
            <h3>Aktivitas terkini</h3>
            <Link to={ROUTES.inbox} style={{ fontSize: 13 }}>Inbox →</Link>
          </div>
          {!recent.length && <p className="muted">Belum ada pesan.</p>}
          {recent.map((m) => (
            <div key={m.id} className="list-item">
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{m.chat_number}</div>
                <div className="muted" style={{ fontSize: 13, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 220 }}>{m.body}</div>
              </div>
              <Badge>{m.direction}</Badge>
            </div>
          ))}
        </Card>
      </div>
    </div>
  )
}
