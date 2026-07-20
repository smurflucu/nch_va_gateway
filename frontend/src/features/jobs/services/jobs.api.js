import { api } from '@/services/api'

const BASE = '/api/v1/jobs'

export const jobsApi = {
  list: () => api.get(BASE),
  tasks: () => api.get(`${BASE}/tasks`),
  create: (payload) => api.post(BASE, payload),
  update: (id, payload) => api.patch(`${BASE}/${id}`, payload),
  remove: (id) => api.delete(`${BASE}/${id}`),
  runNow: (id) => api.post(`${BASE}/${id}/run`),
  history: (id) => api.get(`${BASE}/${id}/runs`),
}
