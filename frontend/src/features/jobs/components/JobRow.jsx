import { useState } from 'react'
import Button from '@/components/ui/Button'
import JobHistory from './JobHistory'

export default function JobRow({ job, onToggle, onRunNow, onUpdateCron }) {
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [cron, setCron] = useState(job.cron)
  const [cronError, setCronError] = useState('')

  const saveCron = async () => {
    const err = await onUpdateCron(job, cron)
    if (err) setCronError(err)
    else {
      setCronError('')
      setEditing(false)
    }
  }

  return (
    <div style={{ borderTop: '1px solid var(--border)', padding: '14px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
        <span
          title={job.enabled ? 'Aktif' : 'Nonaktif'}
          style={{
            width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
            background: job.enabled ? '#3ecf8e' : 'var(--text-dim)',
          }}
        />
        <div style={{ flex: 1, minWidth: 200 }}>
          <strong>{job.name}</strong>
          <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{job.description || job.task_name}</div>
        </div>

        {editing ? (
          <span style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input
              value={cron}
              onChange={(e) => setCron(e.target.value)}
              style={{ width: 130, padding: '6px 8px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text)', fontFamily: 'monospace' }}
            />
            <Button onClick={saveCron} style={{ padding: '6px 10px' }}>✓</Button>
            <Button variant="ghost" onClick={() => { setEditing(false); setCron(job.cron); setCronError('') }} style={{ padding: '6px 10px' }}>✕</Button>
          </span>
        ) : (
          <code
            onClick={() => setEditing(true)}
            title="Klik untuk edit jadwal"
            style={{ cursor: 'pointer', background: 'var(--bg)', padding: '4px 10px', borderRadius: 6, fontSize: 13 }}
          >
            {job.cron}
          </code>
        )}

        <span style={{ fontSize: 12, color: 'var(--text-dim)', minWidth: 150 }}>
          {job.next_run ? `Next: ${new Date(job.next_run).toLocaleString('id-ID')}` : 'Tidak terjadwal'}
        </span>

        <Button variant="ghost" onClick={() => onRunNow(job)}>▶ Run Now</Button>
        <Button variant="ghost" onClick={() => onToggle(job)}>{job.enabled ? 'Matikan' : 'Aktifkan'}</Button>
        <Button variant="ghost" onClick={() => setOpen(!open)}>{open ? 'Tutup' : 'History'}</Button>
      </div>
      {cronError && <p style={{ color: 'var(--danger)', fontSize: 12, marginTop: 6 }}>{cronError}</p>}
      {open && <div style={{ marginTop: 12 }}><JobHistory jobId={job.id} /></div>}
    </div>
  )
}
