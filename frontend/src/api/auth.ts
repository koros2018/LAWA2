/**
 * LAWA2 — 简化登录 API
 */

import { apiPost } from './client'

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
  token: string
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
  token: string
}

const BASE = '/api/v2/auth'

export async function login(username: string, nativeLang: string): Promise<LoginResult> {
  return apiPost<LoginResult>(`${BASE}/login`, { username, native_lang: nativeLang })
}

export async function saveProfile(data: {
  username: string
  display_name: string
  native_lang: string
  learn_lang: string
  interests: string[]
  current_level: string | null
}): Promise<ProfileResult> {
  return apiPost<ProfileResult>(`${BASE}/profile`, data)
}