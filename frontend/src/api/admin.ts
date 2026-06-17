/**
 * Admin API — 超级管理员 Agent
 * 仅管理员可访问 · Admin-only access
 *
 * 端点:
 *   GET  /api/v2/admin/users        用户列表
 *   GET  /api/v2/admin/users/:id    用户详情
 *   POST /api/v2/admin/users/:id/toggle  切换激活
 *   GET  /api/v2/admin/stats        系统统计
 *   POST /api/v2/admin/users/:id/admin  设置管理员权限
 */

import { apiGet, apiPost } from './client'

export interface SystemStats {
  user_count: number
  active_users_today: number
  total_habit_events: number
  today_habit_events: number
  active_configs: number
  db_size_bytes: number
  daily_trends?: Array<{ date: string; active_users: number; events: number }>
  top_users?: UserAdmin[]
  avg_events_per_user?: number
  new_users_7d?: number
  bridge_interactions?: number
  photos?: number
  push_notifications?: number
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
  is_admin: boolean
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

export interface SetAdminResponse {
  id: string
  username: string
  display_name: string | null
  is_admin: boolean
}

const BASE = '/api/v2/admin'

export async function getAdminStats(): Promise<SystemStats> {
  return apiGet<SystemStats>(`${BASE}/stats`)
}

export async function getAdminUsers(
  limit: number = 20,
  offset: number = 0,
  search?: string,
): Promise<UsersListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (search) params.set('search', search)
  return apiGet<UsersListResponse>(`${BASE}/users?${params}`)
}

export async function getAdminUserDetail(userId: string): Promise<UserAdmin> {
  return apiGet<UserAdmin>(`${BASE}/users/${userId}`)
}

export async function toggleAdminUser(userId: string): Promise<UserAdmin> {
  return apiPost<UserAdmin>(`${BASE}/users/${userId}/toggle`)
}

export async function setAdminStatus(userId: string, isAdmin: boolean): Promise<SetAdminResponse> {
  return apiPost<SetAdminResponse>(`${BASE}/users/${userId}/admin?is_admin=${isAdmin}`)
}