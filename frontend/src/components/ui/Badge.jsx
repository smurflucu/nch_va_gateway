// Peta status -> warna (teks, bg). Selaras dengan token light theme.
const MAP = {
  connected: ['#128a3f', 'var(--success-soft)'],
  connecting: ['#245ce0', 'var(--accent-soft)'],
  qr: ['#b7770a', 'var(--warn-soft)'],
  disconnected: ['#6b7688', 'var(--surface-2)'],
  logged_out: ['#c93a3f', 'var(--danger-soft)'],
  // broadcast / message
  done: ['#128a3f', 'var(--success-soft)'],
  running: ['#245ce0', 'var(--accent-soft)'],
  scheduled: ['#b7770a', 'var(--warn-soft)'],
  pending_approval: ['#b7770a', 'var(--warn-soft)'],
  rejected: ['#c93a3f', 'var(--danger-soft)'],
  failed: ['#c93a3f', 'var(--danger-soft)'],
  draft: ['#6b7688', 'var(--surface-2)'],
  in: ['#128a3f', 'var(--success-soft)'],
  out: ['#245ce0', 'var(--accent-soft)'],
  received: ['#128a3f', 'var(--success-soft)'],
  sent: ['#245ce0', 'var(--accent-soft)'],
}

const LABELS = { pending_approval: 'menunggu approval', logged_out: 'logout' }

export default function Badge({ children }) {
  const [color, bg] = MAP[children] || ['#6b7688', 'var(--surface-2)']
  return (
    <span style={{
      display: 'inline-block', padding: '3px 11px', borderRadius: 20,
      fontSize: 12, fontWeight: 600, color, background: bg, whiteSpace: 'nowrap',
    }}>{LABELS[children] || children}</span>
  )
}
