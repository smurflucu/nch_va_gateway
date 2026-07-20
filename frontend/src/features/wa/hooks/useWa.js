import { useCallback, useEffect, useState } from 'react'
import { waApi } from '../services/wa.api'

function useList(fetcher, { poll, enabled = true } = {}) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const { data } = await fetcher()
      setItems(data)
      setError('')
    } catch (e) {
      setError(e.response?.data?.detail || 'Gagal memuat data')
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!enabled) { setLoading(false); return }
    refresh()
    if (poll) {
      const t = setInterval(refresh, poll)
      return () => clearInterval(t)
    }
  }, [refresh, poll, enabled])

  return { items, loading, error, refresh, setItems }
}

export const useSessions = () => useList(waApi.listSessions, { poll: 5000 })
export const useContacts = () => useList(waApi.listContacts)
export const useTemplates = () => useList(waApi.listTemplates)
export const useBroadcasts = () => useList(waApi.listBroadcasts, { poll: 5000 })
export const useAutoReplies = () => useList(waApi.listAutoReplies)
export const useApiKeys = () => useList(waApi.listApiKeys)
export const useUsers = () => useList(waApi.listUsers)
export const useSupervisors = (enabled = true) => useList(waApi.listSupervisors, { enabled })
export const usePendingBroadcasts = (enabled = true) =>
  useList(waApi.listPendingBroadcasts, { poll: 8000, enabled })

export function useInbox() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('') // '' | 'in' | 'out'

  const refresh = useCallback(async () => {
    try {
      const { data } = await waApi.listMessages(filter || undefined)
      setItems(data)
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 5000)
    return () => clearInterval(t)
  }, [refresh])

  return { items, loading, filter, setFilter, refresh }
}
