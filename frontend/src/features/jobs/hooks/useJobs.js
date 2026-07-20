import { useCallback, useEffect, useState } from 'react'
import { jobsApi } from '../services/jobs.api'

export function useJobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const { data } = await jobsApi.list()
      setJobs(data)
      setError('')
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal memuat jobs')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 15000) // auto-refresh tiap 15 detik
    return () => clearInterval(t)
  }, [refresh])

  const toggle = async (job) => {
    await jobsApi.update(job.id, { enabled: !job.enabled })
    refresh()
  }

  const updateCron = async (job, cron) => {
    try {
      await jobsApi.update(job.id, { cron })
      refresh()
      return null
    } catch (e) {
      return e.response?.data?.detail || 'Cron invalid'
    }
  }

  const runNow = async (job) => {
    await jobsApi.runNow(job.id)
    setTimeout(refresh, 2000)
  }

  return { jobs, loading, error, refresh, toggle, updateCron, runNow }
}
