/**
 * Admin API — 超级管理员 Agent
 *
 * 端点:
 *   GET  /api/v2/admin/users        用户列表
 *   GET  /api/v2/admin/users/:id    用户详情
 *   POST /api/v2/admin/users/:id/toggle  切换激活
 *   GET  /api/v2/admin/stats        系统统计
 */

export interface SystemStats {
  user_count: number
  active_users_today: number
  total_habit_events: number
  today_habit_events: number
  active_configs: number
  db_size_bytes: number
}

export interface UserAdmin {
  id: string
  username: string
  display_name: string | null
  native_lang: string
  learn_lang: string
  current_level: string | null
  habit_level: number
  growth_xp: number
  streak_days: number
  bridge_level: number
  is_active: boolean
  interests: string[]
  created_at: string
  updated_at: string
}

export interface UsersListResponse {
  users: UserAdmin[]
  total: number
  limit: number
  offset: number
}

const BASE = '/api/v2/admin'

async function apiFetch<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(url, opts)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const json = await res.json()
  if (json.status !== 'ok') throw new Error(json.detail || 'API error')
  return json.data as T
}

export async function getAdminStats(): Promise<SystemStats> {
  return apiFetch<SystemStats>(`${BASE}/stats`)
}

export async function getAdminUsers(
  limit: number = 20,
  offset: number = 0,
  search?: string,
): Promise<UsersListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (search) params.set('search', search)
  return apiFetch<UsersListResponse>(`${BASE}/users?${params}`)
}

export async function getAdminUserDetail(userId: string): Promise<UserAdmin> {
  return apiFetch<UserAdmin>(`${BASE}/users/${userId}`)
}

export async function toggleAdminUser(userId: string): Promise<UserAdmin> {
  return apiFetch<UserAdmin>(`${BASE}/users/${userId}/toggle`, { method: 'POST' })
}
