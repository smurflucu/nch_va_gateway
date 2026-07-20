import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { useContacts, waApi } from '@/features/wa'

export default function ContactsPage() {
  const { items, loading, refresh } = useContacts()
  const [form, setForm] = useState({ name: '', phone: '', tags: '' })
  const [err, setErr] = useState('')

  const add = async () => {
    setErr('')
    try {
      await waApi.createContact(form)
      setForm({ name: '', phone: '', tags: '' })
      refresh()
    } catch (e) {
      setErr(e.response?.data?.detail || 'Gagal simpan')
    }
  }

  const remove = async (id) => {
    await waApi.deleteContact(id)
    refresh()
  }

  return (
    <div>
      <h1 style={{ marginBottom: 18 }}>Kontak</h1>
      <Card style={{ marginBottom: 18 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 10, alignItems: 'end' }}>
          <Input label="Nama" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Nomor" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="0812…" />
          <Input label="Tag (koma)" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="vip, jakarta" />
          <div style={{ marginBottom: 14 }}><Button onClick={add} disabled={!form.phone}>+ Tambah</Button></div>
        </div>
        {err && <p style={{ color: 'var(--danger)', fontSize: 13 }}>{err}</p>}
      </Card>

      <Card>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Memuat…</p>}
        {!loading && !items.length && <p style={{ color: 'var(--text-dim)' }}>Belum ada kontak.</p>}
        {items.map((c) => (
          <div key={c.id} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 0', borderBottom: '1px solid var(--border)',
          }}>
            <div>
              <div style={{ fontWeight: 600 }}>{c.name || '(tanpa nama)'}</div>
              <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>{c.phone}{c.tags ? ` · ${c.tags}` : ''}</div>
            </div>
            <Button variant="ghost" onClick={() => remove(c.id)}>Hapus</Button>
          </div>
        ))}
      </Card>
    </div>
  )
}
