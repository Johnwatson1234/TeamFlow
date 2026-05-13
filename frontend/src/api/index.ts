import axios, { type AxiosRequestConfig } from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err.response?.data || err)
  }
)

const api = {
  get<T = any>(url: string, config?: AxiosRequestConfig) {
    return request.get<any, T>(url, config)
  },
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return request.post<any, T>(url, data, config)
  },
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return request.put<any, T>(url, data, config)
  },
  delete<T = any>(url: string, config?: AxiosRequestConfig) {
    return request.delete<any, T>(url, config)
  },
}

export default api

// Auth
export const authApi = {
  register: (data: any) => api.post('/auth/register', data),
  login: (data: any) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  updateMe: (data: any) => api.put('/auth/me', data),
  searchUsers: (q: string) => api.get('/auth/users/search', { params: { q } }),
}

// Projects
export const projectApi = {
  list: () => api.get('/projects'),
  create: (data: any) => api.post('/projects', data),
  get: (id: number) => api.get(`/projects/${id}`),
  update: (id: number, data: any) => api.put(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
  dashboard: (id: number) => api.get(`/projects/${id}/dashboard`),
  members: (id: number) => api.get(`/projects/${id}/members`),
  inviteMember: (id: number, data: any) => api.post(`/projects/${id}/members`, data),
  removeMember: (id: number, userId: number) => api.delete(`/projects/${id}/members/${userId}`),
}

// Tasks
export const taskApi = {
  list: (projectId: number, status?: string) => api.get(`/projects/${projectId}/tasks`, { params: { status } }),
  create: (projectId: number, data: any) => api.post(`/projects/${projectId}/tasks`, data),
  get: (id: number) => api.get(`/tasks/${id}`),
  update: (id: number, data: any) => api.put(`/tasks/${id}`, data),
  delete: (id: number) => api.delete(`/tasks/${id}`),
  milestones: (projectId: number) => api.get(`/projects/${projectId}/milestones`),
  createMilestone: (projectId: number, data: any) => api.post(`/projects/${projectId}/milestones`, data),
}

// Messages
export const messageApi = {
  list: (projectId: number, threadId?: number, limit = 50, offset = 0) =>
    api.get(`/projects/${projectId}/messages`, { params: { thread_id: threadId, limit, offset } }),
  send: (projectId: number, data: any) => api.post(`/projects/${projectId}/messages`, data),
  delete: (id: number) => api.delete(`/messages/${id}`),
}

// Documents
export const documentApi = {
  list: (projectId: number) => api.get(`/projects/${projectId}/documents`),
  create: (projectId: number, data: any) => api.post(`/projects/${projectId}/documents`, data),
  get: (id: number) => api.get(`/documents/${id}`),
  update: (id: number, data: any) => api.put(`/documents/${id}`, data),
  delete: (id: number) => api.delete(`/documents/${id}`),
  versions: (id: number) => api.get(`/documents/${id}/versions`),
  saveVersion: (id: number, data: any) => api.post(`/documents/${id}/versions`, data),
}

// Files
export const fileApi = {
  list: (projectId: number) => api.get(`/projects/${projectId}/files`),
  upload: (projectId: number, file: File, taskId?: number) => {
    const form = new FormData()
    form.append('file', file)
    if (taskId) form.append('related_task_id', String(taskId))
    return api.post(`/projects/${projectId}/files/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (id: number) => api.delete(`/files/${id}`),
}

// Collaboration
export const collabApi = {
  graph: (projectId: number) => api.get(`/projects/${projectId}/graph`),
  contribution: (projectId: number) => api.get(`/projects/${projectId}/contribution`),
  recalculate: (projectId: number) => api.post(`/projects/${projectId}/contribution/recalculate`),
  riskAlerts: (projectId: number) => api.get(`/projects/${projectId}/risk-alerts`),
  scanRisks: (projectId: number) => api.post(`/projects/${projectId}/risk-alerts/scan`),
  resolveAlert: (alertId: number) => api.put(`/risk-alerts/${alertId}/resolve`),
  commits: (projectId: number) => api.get(`/projects/${projectId}/git/commits`),
  addCommit: (projectId: number, data: any) => api.post(`/projects/${projectId}/git/commits`, data),
  peerEvals: (projectId: number) => api.get(`/projects/${projectId}/peer-evaluations`),
  submitPeerEval: (projectId: number, data: any) => api.post(`/projects/${projectId}/peer-evaluations`, data),
}

// AI
export const aiApi = {
  planning: (projectId: number, data: any) =>
    api.post(`/ai/planning?project_id=${projectId}`, data),
  confirmPlanning: (suggestionId: number) =>
    api.post(`/ai/planning/${suggestionId}/confirm`),
  weeklyReport: (projectId: number) =>
    api.post(`/ai/reports/weekly?project_id=${projectId}`),
}
