import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import { useAuthStore } from '@/features/auth'
import { useUsers, useSupervisors, waApi } from '@/features/wa'

function RoleChip({ role }) {
  return <span className={`role-chip role-${role}`}>{role}</span>
}

/** Modal edit user (admin) */
function EditUserModal({ user, me, supervisors, onClose, onSaved }) {
  const isSelf = user.id === me.id
  const [full_name, setFullName] = useState(user.full_name || '')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState(user.role)
  const [supervisorId, setSupervisorId] = useState(user.supervisor_id || '')
  const [isActive, setIsActive] = useState(user.is_active)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const save = async () => {
    if (password && password.length < 8) { setErr('Password minimal 8 karakter'); return }
    if (!isSelf && role === 'user' && !supervisorId) { setErr('Regular user wajib punya supervisor'); return }
    setBusy(true); setErr('')
    try {
      const payload = { full_name }
      if (password) payload.password = password
      if (!isSelf) {
        payload.role = role
        payload.is_active = isActive
        if (role === 'user') payload.supervisor_id = Number(supervisorId)
      }
      await waApi.updateUser(user.id, payload)
      onSaved()
      onClose()
    } catch (e) {
      setErr(e.response?.data?.detail || 'Gagal menyimpan')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(16,24,40,.45)', zIndex: 100,
      display: 'grid', placeItems: 'center', padding: 20,
    }}>
      <Card onClick={(e) => e.stopPropagation()} style={{ width: 400, maxWidth: '100%' }}>
        <div className="row-between" style={{ marginBottom: 14 }}>
          <h3>Edit user</h3>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>

        <Input label="Nama lengkap" value={full_name} onChange={(e) => setFullName(e.target.value)} />
        <Input label="Password baru (kosongkan jika tak diubah)" type="password" value={password}
               onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />

        {isSelf ? (
          <p className="muted" style={{ fontSize: 12, marginBottom: 12 }}>
            Role, supervisor, dan status akun sendiri tidak bisa diubah dari sini.
          </p>
        ) : (
          <>
            <Select label="Role" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="user">Regular user</option>
              <option value="supervisor">Supervisor</option>
              <option value="admin">Admin</option>
            </Select>
            {role === 'user' && (
              <Select label="Supervisor (tim)" value={supervisorId} onChange={(e) => setSupervisorId(e.target.value)}>
                <option value="">— pilih supervisor —</option>
                {supervisors.map((s) => <option key={s.id} value={s.id}>{s.full_name || s.email}</option>)}
              </Select>
            )}
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '2px 0 14px', fontSize: 14 }}>
              <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
              Akun aktif
            </label>
          </>
        )}

        {err && <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 10 }}>{err}</p>}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <Button variant="ghost" onClick={onClose}>Batal</Button>
          <Button onClick={save} disabled={busy}>{busy ? 'Menyimpan…' : 'Simpan'}</Button>
        </div>
      </Card>
    </div>
  )
}

export default function TeamPage() {
  const me = useAuthStore((s) => s.user)
  const isAdmin = me.role === 'admin'
  const { items: users, loading, refresh } = useUsers()
  const { items: supervisors, refresh: refreshSups } = useSupervisors(isAdmin)

  // Setiap perubahan user bisa mengubah nama/daftar supervisor → refresh keduanya
  // supaya dropdown supervisor tidak menampilkan nama lama.
  const reload = () => { refresh(); refreshSups() }

  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'user', supervisor_id: '' })
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)
  const [editing, setEditing] = useState(null)

  const submit = async () => {
    setBusy(true); setMsg(null)
    try {
      if (isAdmin) {
        const payload = { email: form.email, password: form.password, full_name: form.full_name, role: form.role }
        if (form.role === 'user') payload.supervisor_id = Number(form.supervisor_id)
        await waApi.createUser(payload)
      } else {
        await waApi.createTeamMember({ email: form.email, password: form.password, full_name: form.full_name })
      }
      setForm({ email: '', password: '', full_name: '', role: 'user', supervisor_id: '' })
      setMsg({ ok: true, text: 'User dibuat ✅' })
      reload()
    } catch (e) {
      setMsg({ ok: false, text: e.response?.data?.detail || 'Gagal membuat user' })
    } finally {
      setBusy(false)
    }
  }

  const changeRole = async (u, role) => { await waApi.updateUser(u.id, { role }); reload() }
  const changeSupervisor = async (u, supervisor_id) => { await waApi.updateUser(u.id, { supervisor_id: Number(supervisor_id) }); reload() }
  const remove = async (u) => {
    if (!confirm(`Hapus user ${u.email}?`)) return
    await waApi.deleteUser(u.id)
    reload()
  }

  const canSubmit = form.email && form.password.length >= 8 &&
    (!isAdmin || form.role !== 'user' || form.supervisor_id)

  return (
    <div>
      <div className="page-head">
        <h1>Tim &amp; User</h1>
        <p>
          {isAdmin
            ? 'Kelola semua user. Buat supervisor, lalu tambahkan regular user ke timnya.'
            : 'Anggota tim Anda. Tambah regular user untuk operasional harian.'}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 320px', gap: 18, alignItems: 'start' }}>
        {/* Tabel user */}
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Nama</th><th>Role</th>{isAdmin && <th>Supervisor</th>}<th>Status</th><th></th>
                </tr>
              </thead>
              <tbody>
                {loading && <tr><td colSpan={5} className="muted">Memuat…</td></tr>}
                {!loading && !users.length && <tr><td colSpan={5} className="muted">Belum ada user.</td></tr>}
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div className="avatar">{(u.full_name || u.email).slice(0, 2).toUpperCase()}</div>
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontWeight: 600 }}>{u.full_name || '—'} {u.id === me.id && <span className="muted" style={{ fontWeight: 400 }}>(Anda)</span>}</div>
                          <div className="muted" style={{ fontSize: 12 }}>{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      {isAdmin && u.id !== me.id ? (
                        <select className="field" style={{ padding: '5px 8px', width: 'auto' }}
                                value={u.role} onChange={(e) => changeRole(u, e.target.value)}>
                          <option value="admin">admin</option>
                          <option value="supervisor">supervisor</option>
                          <option value="user">user</option>
                        </select>
                      ) : <RoleChip role={u.role} />}
                    </td>
                    {isAdmin && (
                      <td>
                        {u.role === 'user' ? (
                          <select className="field" style={{ padding: '5px 8px', width: 'auto' }}
                                  value={u.supervisor_id || ''} onChange={(e) => changeSupervisor(u, e.target.value)}>
                            <option value="" disabled>— pilih —</option>
                            {supervisors.map((s) => <option key={s.id} value={s.id}>{s.full_name || s.email}</option>)}
                          </select>
                        ) : <span className="muted">—</span>}
                      </td>
                    )}
                    <td>{u.is_active ? <span style={{ color: 'var(--success)' }}>● aktif</span> : <span className="muted">● nonaktif</span>}</td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                      {isAdmin && (
                        <>
                          <Button variant="ghost" size="sm" onClick={() => setEditing(u)}>Edit</Button>
                          {u.id !== me.id && (
                            <Button variant="ghost" size="sm" style={{ marginLeft: 6, color: 'var(--danger)' }} onClick={() => remove(u)}>Hapus</Button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Form tambah */}
        <Card>
          <h3 style={{ marginBottom: 14 }}>{isAdmin ? 'Tambah user' : 'Tambah anggota tim'}</h3>
          <Input label="Nama lengkap" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Budi" />
          <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="budi@perusahaan.com" />
          <Input label="Password (min 8)" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          {isAdmin && (
            <>
              <Select label="Role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="user">Regular user</option>
                <option value="supervisor">Supervisor</option>
                <option value="admin">Admin</option>
              </Select>
              {form.role === 'user' && (
                <Select label="Supervisor (tim)" value={form.supervisor_id} onChange={(e) => setForm({ ...form, supervisor_id: e.target.value })}>
                  <option value="">— pilih supervisor —</option>
                  {supervisors.map((s) => <option key={s.id} value={s.id}>{s.full_name || s.email}</option>)}
                </Select>
              )}
            </>
          )}
          <Button style={{ width: '100%' }} disabled={busy || !canSubmit} onClick={submit}>
            {busy ? 'Menyimpan…' : '+ Buat user'}
          </Button>
          {msg && <p style={{ marginTop: 10, fontSize: 13, color: msg.ok ? 'var(--success)' : 'var(--danger)' }}>{msg.text}</p>}
        </Card>
      </div>

      {editing && (
        <EditUserModal
          user={editing} me={me} supervisors={supervisors}
          onClose={() => setEditing(null)}
          onSaved={reload}
        />
      )}
    </div>
  )
}
