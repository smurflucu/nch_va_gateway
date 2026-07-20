import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Textarea from '@/components/ui/Textarea'
import { useTemplates, waApi } from '@/features/wa'

export default function TemplatesPage() {
  const { items, loading, refresh } = useTemplates()
  const [form, setForm] = useState({ name: '', body: '' })

  const add = async () => {
    if (!form.name || !form.body) return
    await waApi.createTemplate(form)
    setForm({ name: '', body: '' })
    refresh()
  }

  return (
    <div>
      <h1 style={{ marginBottom: 6 }}>Template Pesan</h1>
      <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 18 }}>
        Gunakan <code>{'{{name}}'}</code> untuk personalisasi saat broadcast.
      </p>

      <Card style={{ marginBottom: 18 }}>
        <Input label="Nama template" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <Textarea label="Isi" value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })}
                  placeholder="Halo {{name}}, ada promo spesial untukmu!" />
        <Button onClick={add} disabled={!form.name || !form.body}>+ Simpan</Button>
      </Card>

      <Card>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Memuat…</p>}
        {!loading && !items.length && <p style={{ color: 'var(--text-dim)' }}>Belum ada template.</p>}
        {items.map((t) => (
          <div key={t.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>{t.name}</strong>
              <Button variant="ghost" onClick={() => { waApi.deleteTemplate(t.id).then(refresh) }}>Hapus</Button>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: 14, marginTop: 6, whiteSpace: 'pre-wrap' }}>{t.body}</p>
          </div>
        ))}
      </Card>
    </div>
  )
}
