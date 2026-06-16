/**
 * LAWA2 — 统一 API 封装
 *
 * 所有前端 API 调用通过此模块发起，自动携带：
 *   - Authorization: Bearer <JWT token>
 *   - Content-Type: application/json
 *   - Token 过期自动刷新（401 → refresh → retry）
 */

const STORAGE_KEY = 'lawa2_session'

interface ApiResponse<T> {
  status: string
  data: T
  message?: string
}

export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const s = JSON.parse(raw)
      if (s?.token) {
        headers['Authorization'] = `Bearer ${s.token}`
      }
    }
  } catch {
    // ignore parse errors
  }
  return headers
}

export function getUserId(): string {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return ''
    const s = JSON.parse(raw)
    return s?.userId || ''
  } catch {
    return ''
  }
}

export function getStoredToken(): string {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return ''
    const s = JSON.parse(raw)
    return s?.token || ''
  } catch {
    return ''
  }
}

/** 尝试刷新 token */
async function tryRefreshToken(): Promise<boolean> {
  const uid = getUserId()
  const oldToken = getStoredToken()
  if (!uid || !oldToken) return false
  try {
    const res = await fetch(`/api/v2/auth/refresh?user_id=${uid}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${oldToken}` },
    })
    if (!res.ok) return false
    const json = await res.json()
    if (json.status === 'ok' && json.data?.token) {
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (raw) {
          const s = JSON.parse(raw)
          s.token = json.data.token
          localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
        }
      } catch { /* ignore */ }
      return true
    }
    return false
  } catch {
    return false
  }
}

/** 刷新 token 的 Promise，确保多个请求不重复刷新 */
let _refreshPromise: Promise<boolean> | null = null

async function refreshTokenOnce(): Promise<boolean> {
  if (_refreshPromise) return _refreshPromise
  _refreshPromise = tryRefreshToken()
  const result = await _refreshPromise
  _refreshPromise = null
  return result
}

async function apiRequest<T>(
  method: string,
  path: string,
  body?: unknown,
  isFormData = false,
): Promise<T> {
  const headers = isFormData
    ? (() => {
        const h = getAuthHeaders()
        delete h['Content-Type']
        return h as Record<string, string>
      })()
    : getAuthHeaders()

  const opts: RequestInit = { method, headers }
  if (body !== undefined && !isFormData) {
    opts.body = JSON.stringify(body)
  }
  if (isFormData) {
    opts.body = body as FormData
  }

  const res = await fetch(path, opts)

  // Token 过期 — 尝试刷新后重试一次
  if (res.status === 401) {
    const refreshed = await refreshTokenOnce()
    if (refreshed) {
      const newHeaders = isFormData
        ? (() => {
            const h = getAuthHeaders()
            delete h['Content-Type']
            return h as Record<string, string>
          })()
        : getAuthHeaders()
      const retryOpts: RequestInit = { method, headers: newHeaders }
      if (body !== undefined && !isFormData) retryOpts.body = JSON.stringify(body)
      if (isFormData) retryOpts.body = body as FormData
      const retryRes = await fetch(path, retryOpts)
      if (!retryRes.ok) throw new Error(`API error: HTTP ${retryRes.status}`)
      const retryJson: ApiResponse<T> = await retryRes.json()
      if (retryJson.status !== 'ok') throw new Error(retryJson.message || 'API unavailable')
      return retryJson.data
    }
    // 刷新失败 — 清除 session 跳转登录
    try {
      localStorage.removeItem(STORAGE_KEY)
      window.location.href = '/login'
    } catch { /* ignore */ }
    throw new Error('Session expired')
  }

  if (!res.ok) throw new Error(`API error: HTTP ${res.status}`)
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error(json.message || 'API unavailable')
  return json.data
}

export async function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>('GET', path)
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiRequest<T>('POST', path, body)
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>('PUT', path, body)
}

export async function apiDelete<T>(path: string): Promise<T> {
  return apiRequest<T>('DELETE', path)
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  return apiRequest<T>('POST', path, formData, true)
}