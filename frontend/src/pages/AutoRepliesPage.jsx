import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Textarea from '@/components/ui/Textarea'
import Badge from '@/components/ui/Badge'
import { useAutoReplies, useSessions, waApi } from '@/features/wa'

const MATCH_LABEL = { equals: 'sama persis', contains: 'mengandung', starts_with: 'diawali' }

export default function AutoRepliesPage() {
  const { items, loading, refresh } = useAutoReplies()
  const { items: sessions } = useSessions()
  const [form, setForm] = useState({ session_id: '', match_type: 'contains', keyword: '', reply_body: '', delay_seconds: 0 })

  const add = async () => {
    if (!form.keyword || !form.reply_body) return
    await waApi.createAutoReply({
      ...form,
      session_id: form.session_id ? Number(form.session_id) : null,
      delay_seconds: Number(form.delay_seconds) || 0,
    })
    setForm({ session_id: '', match_type: 'contains', keyword: '', reply_body: '', delay_seconds: 0 })
    refresh()
  }

  const toggle = async (r) => { await waApi.updateAutoReply(r.id, { enabled: !r.enabled }); refresh() }
  const remove = async (r) => { await waApi.deleteAutoReply(r.id); refresh() }

  return (
    <div>
      <h1 style={{ marginBottom: 6 }}>Auto-Reply</h1>
      <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 18 }}>
        Balas otomatis pesan masuk berdasarkan kata kunci. Aturan pertama yang cocok yang dipakai.
      </p>

      <Card style={{ marginBottom: 18 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
          <Select label="Berlaku untuk" value={form.session_id} onChange={(e) => setForm({ ...form, session_id: e.target.value })}>
            <option value="">Semua nomor</option>
            {sessions.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </Select>
          <Select label="Kecocokan" value={form.match_type} onChange={(e) => setForm({ ...form, match_type: e.target.value })}>
            <option value="contains">mengandung</option>
            <option value="equals">sama persis</option>
            <option value="starts_with">diawali</option>
          </Select>
          <Input label="Kata kunci" value={form.keyword} onChange={(e) => setForm({ ...form, keyword: e.target.value })} placeholder="harga" />
        </div>
        <Textarea label="Balasan otomatis" value={form.reply_body} onChange={(e) => setForm({ ...form, reply_body: e.target.value })}
                  placeholder="Terima kasih! Daftar harga: …" />
        <div style={{ maxWidth: 280 }}>
          <Input label="Jeda sebelum balas (detik)" type="number" min={0} max={300}
                 value={form.delay_seconds} onChange={(e) => setForm({ ...form, delay_seconds: e.target.value })} />
        </div>
        <p className="muted" style={{ fontSize: 12, marginTop: -6, marginBottom: 14 }}>
          0 = balas langsung. Beri jeda (mis. 3–15 dtk) supaya tidak terlihat seperti bot — mengurangi risiko banned.
        </p>
        <Button onClick={add} disabled={!form.keyword || !form.reply_body}>+ Tambah aturan</Button>
      </Card>

      <Card>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Memuat…</p>}
        {!loading && !items.length && <p style={{ color: 'var(--text-dim)' }}>Belum ada aturan.</p>}
        {items.map((r) => (
          <div key={r.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontWeight: 600 }}>
                {MATCH_LABEL[r.match_type]} "<span style={{ color: 'var(--accent)' }}>{r.keyword}</span>"
                {r.delay_seconds > 0 && (
                  <span className="muted" style={{ fontWeight: 400, fontSize: 13, marginLeft: 8 }}>
                    · jeda {r.delay_seconds} dtk
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <Badge>{r.enabled ? 'aktif' : 'nonaktif'}</Badge>
                <Button variant="ghost" onClick={() => toggle(r)}>{r.enabled ? 'Matikan' : 'Aktifkan'}</Button>
                <Button variant="danger" onClick={() => remove(r)}>Hapus</Button>
              </div>
            </div>
            <p style={{ fontSize: 14, color: 'var(--text-dim)', marginTop: 6, whiteSpace: 'pre-wrap' }}>→ {r.reply_body}</p>
          </div>
        ))}
      </Card>
    </div>
  )
}
