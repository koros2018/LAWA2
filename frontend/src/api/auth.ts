/**
 * LAWA2 — 简化登录 API
 */

const API_BASE = '/api/v2/auth'

interface ApiResponse<T> {
  status: string
  data: T
}

async function api<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error('API unavailable')
  return json.data
}

export interface LoginResult {
  user_id: string
  username: string
  display_name: string
  native_lang: string
  learn_lang: string
  interests?: string[]
  current_level?: string | null
  has_profile: boolean
  is_new_user: boolean
  token: string  // JWT token
}

export interface ProfileResult {
  user_id: string
  username: string
  display_name: string
  native_lang: string
  learn_lang: string
  interests: string[]
  current_level: string | null
  is_new_user: boolean
  token: string  // JWT token
}

export async function login(username: string, nativeLang: string): Promise<LoginResult> {
  return api<LoginResult>('/login', { username, native_lang: nativeLang })
}

export async function saveProfile(data: {
  username: string
  display_name: string
  native_lang: string
  learn_lang: string
  interests: string[]
  current_level: string | null
}): Promise<ProfileResult> {
  return api<ProfileResult>('/profile', data)
}