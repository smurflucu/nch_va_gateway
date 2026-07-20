import { useEffect, useState } from 'react'
import { authApi } from '../services/auth.api'
import { useAuthStore } from '../store/auth.store'

export async function login(email, password) {
  const { data } = await authApi.login(email, password)
  useAuthStore.getState().setAccessToken(data.access_token)
  const { data: user } = await authApi.me()
  useAuthStore.getState().setAuth(user, data.access_token)
  return user
}

export async function logout() {
  try {
    await authApi.logout()
  } finally {
    useAuthStore.getState().clear()
  }
}

/** Restore session dari refresh cookie waktu app pertama load. */
export function useRestoreSession() {
  useEffect(() => {
    const store = useAuthStore.getState()
    ;(async () => {
      try {
        const { data } = await authApi.refresh()
        store.setAccessToken(data.access_token)
        const { data: user } = await authApi.me()
        store.setAuth(user, data.access_token)
      } catch {
        store.clear()
      } finally {
        store.setInitialized()
      }
    })()
  }, [])
}

export function useLogin() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (email, password) => {
    setLoading(true)
    setError('')
    try {
      return await login(email, password)
    } catch (e) {
      setError(e.response?.data?.detail || 'Login gagal, coba lagi')
      return null
    } finally {
      setLoading(false)
    }
  }
  return { submit, loading, error }
}
