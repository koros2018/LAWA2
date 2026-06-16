/**
 * LAWA2 — 简单状态管理（reactive store，无 Pinia 依赖）
 */

import { reactive } from 'vue'

export interface UserSession {
  userId: string
  username: string
  displayName: string
  nativeLang: string
  learnLang: string
  interests: string[]
  currentLevel: string | null
  hasProfile: boolean
  isNewUser: boolean
}

const STORAGE_KEY = 'lawa2_session'

function loadSession(): UserSession | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as UserSession
  } catch {
    return null
  }
}

function saveSession(s: UserSession) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY)
  session.user = null
}

const saved = loadSession()

export const session = reactive<{ user: UserSession | null }>({
  user: saved,
})

export function setSession(data: {
  user_id: string
  username: string
  display_name: string
  native_lang: string
  learn_lang: string
  interests?: string[]
  current_level?: string | null
  has_profile: boolean
  is_new_user: boolean
}) {
  const s: UserSession = {
    userId: data.user_id,
    username: data.username,
    displayName: data.display_name,
    nativeLang: data.native_lang,
    learnLang: data.learn_lang,
    interests: data.interests || [],
    currentLevel: data.current_level || null,
    hasProfile: data.has_profile,
    isNewUser: data.is_new_user,
  }
  session.user = s
  saveSession(s)
}

export function updateProfile(data: {
  display_name: string
  native_lang: string
  learn_lang: string
  interests: string[]
  current_level?: string | null
}) {
  if (!session.user) return
  Object.assign(session.user, {
    displayName: data.display_name,
    nativeLang: data.native_lang,
    learnLang: data.learn_lang,
    interests: data.interests,
    currentLevel: data.current_level || null,
    hasProfile: true,
    isNewUser: false,
  })
  saveSession(session.user)
}