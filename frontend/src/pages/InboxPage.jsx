import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { useInbox } from '@/features/wa'

export default function InboxPage() {
  const { items, loading, filter, setFilter } = useInbox()

  const Tab = ({ value, label }) => (
    <Button variant={filter === value ? 'primary' : 'ghost'} onClick={() => setFilter(value)}>{label}</Button>
  )

  return (
    <div>
      <h1 style={{ marginBottom: 12 }}>Inbox</h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <Tab value="" label="Semua" />
        <Tab value="in" label="Masuk" />
        <Tab value="out" label="Keluar" />
      </div>

      <Card>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Memuat…</p>}
        {!loading && !items.length && <p style={{ color: 'var(--text-dim)' }}>Belum ada pesan.</p>}
        {items.map((m) => (
          <div key={m.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <span style={{ fontWeight: 600 }}>{m.chat_number}</span>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <Badge>{m.direction}</Badge>
                {m.status === 'failed' && <Badge>failed</Badge>}
                <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                  {new Date(m.created_at).toLocaleString('id-ID')}
                </span>
              </div>
            </div>
            <p style={{ fontSize: 14, color: 'var(--text)', whiteSpace: 'pre-wrap' }}>{m.body}</p>
            {m.error && <p style={{ fontSize: 12, color: 'var(--danger)' }}>{m.error}</p>}
          </div>
        ))}
      </Card>
    </div>
  )
}
