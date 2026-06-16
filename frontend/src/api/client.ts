/**
 * LAWA2 — 统一 API 封装
 *
 * 所有前端 API 调用通过此模块发起，自动携带：
 *   - Authorization: Bearer <JWT token>
 *   - Content-Type: application/json
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

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path, {
    method: 'GET',
    headers: getAuthHeaders(),
  })
  if (!res.ok) throw new Error(`API error: HTTP ${res.status}`)
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error(json.message || 'API unavailable')
  return json.data
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`API error: HTTP ${res.status}`)
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error(json.message || 'API unavailable')
  return json.data
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error: HTTP ${res.status}`)
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error(json.message || 'API unavailable')
  return json.data
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(path, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!res.ok) throw new Error(`API error: HTTP ${res.status}`)
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error(json.message || 'API unavailable')
  return json.data
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const headers = getAuthHeaders()
  // FormData 不需要 Content-Type，让浏览器自动设置 boundary
  delete headers['Content-Type']
  const res = await fetch(path, {
    method: 'POST',
    headers,
    body: formData,
  })
  if (!res.ok) throw new Error(`API error: HTTP ${res.status}`)
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error(json.message || 'API unavailable')
  return json.data
}