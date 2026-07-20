import axios from 'axios'

const TOKEN_KEY = 'tfm_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

/**
 * Cliente HTTP único.
 * - Dev: baseURL '/api' → proxy Vite a NestJS (:3000).
 * - Prod: VITE_API_URL apunta al backend en Render/Railway (p. ej. https://tfm-api.onrender.com/api).
 */
const baseURL = import.meta.env.VITE_API_URL || '/api'
export const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && tokenStore.get()) {
      tokenStore.clear()
      if (location.pathname !== '/login') location.assign('/login')
    }
    return Promise.reject(error)
  },
)

/** Extrae un mensaje de error legible de una respuesta de axios. */
export function apiError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: string | string[] } | undefined
    const msg = data?.message
    if (Array.isArray(msg)) return msg.join(', ')
    if (msg) return msg
    return err.message
  }
  return (err as Error)?.message ?? 'Error desconocido'
}
