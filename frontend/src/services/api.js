import axios from 'axios'
import { useAuthStore } from '@/features/auth/store/auth.store'

// Kosong = pakai proxy dev vite / nginx (same-origin). Isi VITE_API_BASE_URL untuk cross-origin.
const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export const api = axios.create({
  baseURL,
  withCredentials: true, // wajib: kirim httpOnly refresh cookie
})

// Request: pasang access token dari MEMORY (zustand), bukan localStorage
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response: kalau 401, coba refresh sekali lalu ulangi request
let refreshing = null
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const isAuthCall = original?.url?.includes('/auth/')
    if (error.response?.status === 401 && !original._retry && !isAuthCall) {
      original._retry = true
      try {
        refreshing = refreshing || api.post('/api/v1/auth/refresh')
        const { data } = await refreshing
        refreshing = null
        useAuthStore.getState().setAccessToken(data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch (e) {
        refreshing = null
        useAuthStore.getState().clear()
      }
    }
    return Promise.reject(error)
  },
)
