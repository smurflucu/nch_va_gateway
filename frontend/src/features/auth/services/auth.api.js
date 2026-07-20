import { api } from '@/services/api'

const BASE = '/api/v1/auth'

export const authApi = {
  login: (email, password) => api.post(`${BASE}/login`, { email, password }),
  register: (payload) => api.post(`${BASE}/register`, payload),
  refresh: () => api.post(`${BASE}/refresh`),
  logout: () => api.post(`${BASE}/logout`),
  me: () => api.get('/api/v1/users/me'),
}
