import { useLocation } from 'react-router-dom'
import { ROUTES } from '@/config/routes'
import { useAuthStore } from '@/features/auth'

const TITLES = {
  [ROUTES.dashboard]: 'Dashboard',
  [ROUTES.sessions]: 'Nomor WhatsApp',
  [ROUTES.send]: 'Kirim Pesan',
  [ROUTES.inbox]: 'Inbox',
  [ROUTES.broadcast]: 'Broadcast',
  [ROUTES.contacts]: 'Kontak',
  [ROUTES.templates]: 'Template',
  [ROUTES.autoreplies]: 'Auto-Reply',
  [ROUTES.team]: 'Tim & User',
  [ROUTES.apikeys]: 'API Gateway',
  [ROUTES.jobs]: 'Jobs',
}

export default function Topbar() {
  const user = useAuthStore((s) => s.user)
  const { pathname } = useLocation()
  const title = TITLES[pathname] || 'Dashboard'
  const initials = (user?.full_name || user?.email || '?').slice(0, 2).toUpperCase()

  return (
    <header style={{
      height: 'var(--topbar-h)', flexShrink: 0, background: 'var(--surface)',
      borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', gap: 16, padding: '0 28px',
      position: 'sticky', top: 0, zIndex: 10,
    }}>
      <div style={{ fontWeight: 650, fontSize: 17 }}>{title}</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ position: 'relative', display: 'none' }} className="topbar-search">
          <input className="field" placeholder="Cari…" style={{ width: 240, paddingLeft: 34 }} />
          <span style={{ position: 'absolute', left: 11, top: 9, color: 'var(--text-dim)' }}>⌕</span>
        </div>
        <div className="avatar" title={user?.email}>{initials}</div>
      </div>
    </header>
  )
}
