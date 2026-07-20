import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import { useAuthStore } from '@/features/auth'
import { useSessions, useSupervisors, QRConnect, waApi } from '@/features/wa'

export default function SessionsPage() {
  const me = useAuthStore((s) => s.user)
  const isAdmin = me.role === 'admin'
  const { items, loading, error, refresh, setItems } = useSessions()
  const { items: supervisors } = useSupervisors(isAdmin)
  const [name, setName] = useState('')
  const [supId, setSupId] = useState('')
  const [busy, setBusy] = useState(false)
  const [active, setActive] = useState(null)

  const supName = (id) => supervisors.find((s) => s.id === id)?.full_name
    || supervisors.find((s) => s.id === id)?.email || null

  const add = async () => {
    if (!name.trim()) return
    setBusy(true)
    try {
      const { data } = await waApi.createSession(name.trim(), supId ? Number(supId) : null)
      setName(''); setSupId('')
      await refresh()
      setActive(data)
    } finally {
      setBusy(false)
    }
  }

  const assign = async (s, supervisor_id) => {
    await waApi.assignSession(s.id, supervisor_id ? Number(supervisor_id) : null)
    refresh()
  }

  const remove = async (s) => {
    if (!confirm(`Hapus sesi "${s.name}"? Nomor akan logout (riwayat pesan tetap tersimpan).`)) return
    try {
      await waApi.deleteSession(s.id)
      setItems((prev) => prev.filter((x) => x.id !== s.id))  // langsung hilang dari UI
    } catch (e) {
      alert(e.response?.data?.detail || 'Gagal menghapus sesi')
    } finally {
      refresh()
    }
  }

  return (
    <div>
      <div className="page-head">
        <h1>Nomor WhatsApp</h1>
        <p>{isAdmin
          ? 'Input nomor, tautkan via QR, lalu assign ke tim supervisor.'
          : 'Nomor yang dialokasikan untuk tim Anda.'}</p>
      </div>

      {isAdmin && (
        <Card style={{ marginBottom: 18 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 220px' }}>
              <Input label="Nama sesi (mis. CS Toko / Marketing)" value={name}
                     onChange={(e) => setName(e.target.value)} placeholder="CS Utama" />
            </div>
            <div style={{ flex: '1 1 200px' }}>
              <label style={{ display: 'block', marginBottom: 14 }}>
                <span style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-dim)', marginBottom: 6 }}>Assign ke tim</span>
                <select className="field" value={supId} onChange={(e) => setSupId(e.target.value)}>
                  <option value="">— belum di-assign —</option>
                  {supervisors.map((s) => <option key={s.id} value={s.id}>{s.full_name || s.email}</option>)}
                </select>
              </label>
            </div>
            <div style={{ marginBottom: 14 }}>
              <Button onClick={add} disabled={busy}>{busy ? 'Membuat…' : '+ Tambah nomor'}</Button>
            </div>
          </div>
        </Card>
      )}

      <Card style={{ padding: 0, overflow: 'hidden' }}>
        {loading && <p className="muted" style={{ padding: 20 }}>Memuat…</p>}
        {error && <p style={{ color: 'var(--danger)', padding: 20 }}>{error}</p>}
        {!loading && !items.length && <p className="muted" style={{ padding: 20 }}>Belum ada nomor.</p>}
        {items.map((s) => (
          <div key={s.id} className="list-item" style={{ padding: '14px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
              <div className="avatar" style={{ background: 'var(--success-soft)', color: 'var(--success)' }}>✆</div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 600 }}>{s.name}</div>
                <div className="muted" style={{ fontSize: 13 }}>
                  {s.phone || 'belum tertaut'}
                  {isAdmin && <> · tim: {supName(s.supervisor_id) || <span style={{ color: 'var(--warn)' }}>belum di-assign</span>}</>}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
              <Badge>{s.status}</Badge>
              {isAdmin && (
                <>
                  <select className="field" style={{ padding: '5px 8px', width: 'auto' }}
                          value={s.supervisor_id || ''} onChange={(e) => assign(s, e.target.value)} title="Assign tim">
                    <option value="">tanpa tim</option>
                    {supervisors.map((sup) => <option key={sup.id} value={sup.id}>{sup.full_name || sup.email}</option>)}
                  </select>
                  {s.status !== 'connected' && <Button variant="ghost" size="sm" onClick={() => setActive(s)}>Scan QR</Button>}
                  <Button variant="danger" size="sm" onClick={() => remove(s)}>Hapus</Button>
                </>
              )}
            </div>
          </div>
        ))}
      </Card>

      {active && <QRConnect session={active} onClose={() => { setActive(null); refresh() }} />}
    </div>
  )
}
