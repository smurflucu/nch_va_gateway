import { useEffect, useState } from 'react'
import { jobsApi } from '../services/jobs.api'

const STATUS_COLOR = { success: '#3ecf8e', failed: 'var(--danger)', running: 'var(--accent)' }

export default function JobHistory({ jobId }) {
  const [runs, setRuns] = useState(null)

  useEffect(() => {
    jobsApi.history(jobId).then(({ data }) => setRuns(data))
  }, [jobId])

  if (!runs) return <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>Memuat history…</p>
  if (!runs.length) return <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>Belum pernah jalan.</p>

  return (
    <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
      <thead>
        <tr style={{ color: 'var(--text-dim)', textAlign: 'left' }}>
          <th style={{ padding: '6px 8px' }}>Mulai</th>
          <th style={{ padding: '6px 8px' }}>Status</th>
          <th style={{ padding: '6px 8px' }}>Durasi</th>
          <th style={{ padding: '6px 8px' }}>Trigger</th>
          <th style={{ padding: '6px 8px' }}>Output</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((r) => (
          <tr key={r.id} style={{ borderTop: '1px solid var(--border)' }}>
            <td style={{ padding: '6px 8px', whiteSpace: 'nowrap' }}>
              {new Date(r.started_at).toLocaleString('id-ID')}
            </td>
            <td style={{ padding: '6px 8px', color: STATUS_COLOR[r.status] }}>{r.status}</td>
            <td style={{ padding: '6px 8px' }}>{r.duration_ms != null ? `${r.duration_ms} ms` : '—'}</td>
            <td style={{ padding: '6px 8px' }}>{r.trigger}</td>
            <td style={{ padding: '6px 8px', maxWidth: 380, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.output}>
              {r.output || '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
