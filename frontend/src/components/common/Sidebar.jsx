import { NavLink, useNavigate } from 'react-router-dom'
import { ROUTES } from '@/config/routes'
import { APP_NAME } from '@/config/constants'
import { useAuthStore, logout } from '@/features/auth'

// roles = daftar role yang boleh melihat menu. undefined = semua role.
const SECTIONS = [
  {
    title: null,
    links: [{ to: ROUTES.dashboard, label: 'Dashboard', icon: '▦' }],
  },
  {
    title: 'WhatsApp',
    links: [
      { to: ROUTES.sessions, label: 'Nomor WA', icon: '☏' },
      { to: ROUTES.send, label: 'Kirim Pesan', icon: '➤' },
      { to: ROUTES.inbox, label: 'Inbox', icon: '✉' },
      { to: ROUTES.broadcast, label: 'Broadcast', icon: '📣' },
    ],
  },
  {
    title: 'Kelola',
    links: [
      { to: ROUTES.contacts, label: 'Kontak', icon: '☰' },
      { to: ROUTES.templates, label: 'Template', icon: '❏' },
      { to: ROUTES.autoreplies, label: 'Auto-Reply', icon: '⟲', roles: ['admin', 'supervisor'] },
      { to: ROUTES.team, label: 'Tim & User', icon: '👥', roles: ['admin', 'supervisor'] },
    ],
  },
  {
    title: 'Sistem',
    roles: ['admin'],
    links: [
      { to: ROUTES.apikeys, label: 'API Gateway', icon: '⚿', roles: ['admin'] },
      { to: ROUTES.jobs, label: 'Jobs', icon: '⏱', roles: ['admin'] },
    ],
  },
]

const linkStyle = ({ isActive }) => ({
  display: 'flex', gap: 11, alignItems: 'center', padding: '9px 12px',
  borderRadius: 10, marginBottom: 2, fontSize: 14, fontWeight: 550,
  color: isActive ? 'var(--accent)' : 'var(--text)',
  background: isActive ? 'var(--accent-soft)' : 'transparent',
})

export default function Sidebar() {
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const role = user?.role || 'user'

  const can = (roles) => !roles || roles.includes(role)
  const initials = (user?.full_name || user?.email || '?').slice(0, 2).toUpperCase()

  const handleLogout = async () => {
    await logout()
    navigate(ROUTES.login)
  }

  return (
    <aside style={{
      width: 'var(--sidebar-w)', flexShrink: 0, background: 'var(--surface)',
      borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column',
      position: 'sticky', top: 0, height: '100vh',
    }}>
      {/* Brand */}
      <div style={{ padding: '18px 18px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9, background: '#25D366',
          display: 'grid', placeItems: 'center', color: '#fff', fontSize: 18,
        }}>✆</div>
        <div style={{ lineHeight: 1.2 }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>{APP_NAME}</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'capitalize' }}>{role}</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '4px 12px' }}>
        {SECTIONS.filter((s) => can(s.roles)).map((sec, i) => {
          const links = sec.links.filter((l) => can(l.roles))
          if (!links.length) return null
          return (
            <div key={i} style={{ marginBottom: 10 }}>
              {sec.title && (
                <div style={{
                  fontSize: 11, fontWeight: 600, color: 'var(--text-dim)',
                  textTransform: 'uppercase', letterSpacing: '.04em', padding: '8px 12px 4px',
                }}>{sec.title}</div>
              )}
              {links.map((l) => (
                <NavLink key={l.to} to={l.to} style={linkStyle}>
                  <span style={{ width: 18, textAlign: 'center', opacity: 0.85 }}>{l.icon}</span>
                  {l.label}
                </NavLink>
              ))}
            </div>
          )
        })}
      </nav>

      {/* User footer */}
      <div style={{ borderTop: '1px solid var(--border)', padding: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px' }}>
          <div className="avatar">{initials}</div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.full_name || 'User'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.email}
            </div>
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" style={{ width: '100%', marginTop: 6, color: 'var(--danger)' }}
                onClick={handleLogout}>⎋ Keluar</button>
      </div>
    </aside>
  )
}
