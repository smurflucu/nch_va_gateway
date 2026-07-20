import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import { useApiKeys, waApi } from '@/features/wa'

export default function ApiKeysPage() {
  const { items, loading, refresh } = useApiKeys()
  const [name, setName] = useState('')
  const [newKey, setNewKey] = useState('')

  const create = async () => {
    const { data } = await waApi.createApiKey(name)
    setNewKey(data.key)
    setName('')
    refresh()
  }

  const remove = async (id) => {
    if (!confirm('Hapus API key ini? Aplikasi yang memakainya akan berhenti berfungsi.')) return
    await waApi.deleteApiKey(id)
    refresh()
  }

  return (
    <div>
      <h1 style={{ marginBottom: 6 }}>API Gateway</h1>
      <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 18 }}>
        Buat API key agar aplikasi lain bisa mengirim pesan lewat gateway ini.
      </p>

      <Card style={{ marginBottom: 18 }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <Input label="Nama key (mis. Aplikasi Toko)" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div style={{ marginBottom: 14 }}><Button onClick={create}>+ Buat key</Button></div>
        </div>
        {newKey && (
          <div style={{ background: 'var(--bg)', border: '1px solid var(--accent)', borderRadius: 8, padding: 12 }}>
            <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 6 }}>
              Simpan sekarang — key hanya ditampilkan sekali:
            </p>
            <code style={{ color: 'var(--accent)', wordBreak: 'break-all' }}>{newKey}</code>
          </div>
        )}
      </Card>

      <Card style={{ marginBottom: 18 }}>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Memuat…</p>}
        {!loading && !items.length && <p style={{ color: 'var(--text-dim)' }}>Belum ada API key.</p>}
        {items.map((k) => (
          <div key={k.id} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 0', borderBottom: '1px solid var(--border)',
          }}>
            <div>
              <div style={{ fontWeight: 600 }}>{k.name || '(tanpa nama)'}</div>
              <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>
                <code>wa_{k.prefix}_••••</code>
                {k.last_used_at ? ` · terakhir dipakai ${new Date(k.last_used_at).toLocaleString('id-ID')}` : ' · belum dipakai'}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Badge>{k.enabled ? 'aktif' : 'nonaktif'}</Badge>
              <Button variant="danger" onClick={() => remove(k.id)}>Hapus</Button>
            </div>
          </div>
        ))}
      </Card>

      <Card>
        <h3 style={{ fontSize: 15, marginBottom: 10 }}>Contoh pemakaian</h3>
        <pre style={{
          background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, padding: 14,
          overflowX: 'auto', fontSize: 13, color: 'var(--text-dim)',
        }}>{`curl -X POST ${location.origin}/api/v1/gateway/send \\
  -H "X-API-Key: wa_xxx_yyy" \\
  -H "Content-Type: application/json" \\
  -d '{"session_id": 1, "to": "0812xxxx", "text": "Halo dari API"}'`}</pre>
      </Card>
    </div>
  )
}
