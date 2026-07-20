import Card from '@/components/ui/Card'
import { useJobs, JobRow } from '@/features/jobs'

export default function JobsPage() {
  const { jobs, loading, error, toggle, updateCron, runNow } = useJobs()

  return (
    <div>
      <h1 style={{ marginBottom: 6 }}>Scheduled Jobs</h1>
      <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 18 }}>
        Pengganti crontab: klik cron expression untuk ubah jadwal, Run Now untuk trigger manual.
      </p>
      <Card>
        {loading && <p style={{ color: 'var(--text-dim)' }}>Memuat…</p>}
        {error && <p style={{ color: 'var(--danger)' }}>{error}</p>}
        {!loading && !jobs.length && <p style={{ color: 'var(--text-dim)' }}>Belum ada job.</p>}
        {jobs.map((j) => (
          <JobRow key={j.id} job={j} onToggle={toggle} onRunNow={runNow} onUpdateCron={updateCron} />
        ))}
      </Card>
    </div>
  )
}
