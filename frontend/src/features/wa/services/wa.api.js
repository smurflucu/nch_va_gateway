import { api } from '@/services/api'

const B = '/api/v1'

export const waApi = {
  // sessions
  listSessions: () => api.get(`${B}/sessions`),
  createSession: (name, supervisorId = null) =>
    api.post(`${B}/sessions`, { name, supervisor_id: supervisorId }),
  assignSession: (id, supervisorId) =>
    api.patch(`${B}/sessions/${id}/assign`, { supervisor_id: supervisorId }),
  sessionStatus: (id) => api.get(`${B}/sessions/${id}/status`),
  reconnect: (id) => api.post(`${B}/sessions/${id}/reconnect`),
  deleteSession: (id) => api.delete(`${B}/sessions/${id}`),

  // messages
  send: (payload) => api.post(`${B}/messages/send`, payload),
  listMessages: (direction) => api.get(`${B}/messages`, { params: direction ? { direction } : {} }),

  // contacts
  listContacts: () => api.get(`${B}/contacts`),
  createContact: (payload) => api.post(`${B}/contacts`, payload),
  deleteContact: (id) => api.delete(`${B}/contacts/${id}`),

  // templates
  listTemplates: () => api.get(`${B}/templates`),
  createTemplate: (payload) => api.post(`${B}/templates`, payload),
  deleteTemplate: (id) => api.delete(`${B}/templates/${id}`),

  // broadcasts
  listBroadcasts: () => api.get(`${B}/broadcasts`),
  listPendingBroadcasts: () => api.get(`${B}/broadcasts/pending`),
  createBroadcast: (payload) => api.post(`${B}/broadcasts`, payload),
  approveBroadcast: (id) => api.post(`${B}/broadcasts/${id}/approve`),
  rejectBroadcast: (id) => api.post(`${B}/broadcasts/${id}/reject`),

  // users / tim
  listUsers: () => api.get(`${B}/users`),
  listSupervisors: () => api.get(`${B}/users/supervisors`),
  createUser: (payload) => api.post(`${B}/users`, payload),
  createTeamMember: (payload) => api.post(`${B}/users/team`, payload),
  updateUser: (id, payload) => api.patch(`${B}/users/${id}`, payload),
  deleteUser: (id) => api.delete(`${B}/users/${id}`),

  // auto replies
  listAutoReplies: () => api.get(`${B}/autoreplies`),
  createAutoReply: (payload) => api.post(`${B}/autoreplies`, payload),
  updateAutoReply: (id, payload) => api.patch(`${B}/autoreplies/${id}`, payload),
  deleteAutoReply: (id) => api.delete(`${B}/autoreplies/${id}`),

  // api keys
  listApiKeys: () => api.get(`${B}/api-keys`),
  createApiKey: (name) => api.post(`${B}/api-keys`, { name }),
  deleteApiKey: (id) => api.delete(`${B}/api-keys/${id}`),
}
