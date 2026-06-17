/**
 * LAWA2 — 拍照 Agent API 封装 (/agent/photo)
 */
const BASE = '/agent/photo'

interface ApiResponse<T> {
  status: string
  data: T
}

function getUserId(): string {
  try {
    const raw = localStorage.getItem('lawa2_session')
    if (!raw) return 'default_user'
    const s = JSON.parse(raw)
    return s?.userId || 'default_user'
  } catch {
    return 'default_user'
  }
}

async function fetchData<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  const json: ApiResponse<T> = await res.json()
  return json.data
}

function withUser(path: string): string {
  const uid = getUserId()
  const sep = path.includes('?') ? '&' : '?'
  return `${BASE}${path}${sep}user_id=${encodeURIComponent(uid)}`
}

// ── 健康检查 ──

export interface AgentHealth {
  status: string
  agent: string
  version: string
}

export async function getPhotoAgentHealth(): Promise<AgentHealth> {
  const res = await fetch(`${BASE}/health`, { headers: { 'Content-Type': 'application/json' } })
  const json = await res.json()
  return json
}

// ── 数据模型 ──

export interface WordItem {
  word: string
  zh: string
  en: string
  example: string
}

export interface PhotoData {
  id: string
  user_id: string
  original_filename: string
  file_size: number
  image_path: string | null
  thumbnail_path?: string | null
  ai_description: string
  ai_description_en: string
  extracted_words: WordItem[]
  scene_tags: string[]
  chat_count: number
  created_at: string
}

export interface PhotoChat {
  id: string
  role: string
  content: string
  content_en: string
  created_at: string
}

export interface ShareResult {
  status: string
  data: {
    interaction_id: string
    xp_earned: number
    message: string
  }
}

// ── API 方法 ──

export async function uploadPhoto(file: File): Promise<PhotoData> {
  const uid = getUserId()
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', uid)
  const res = await fetch(`${BASE}/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  const json: ApiResponse<PhotoData> = await res.json()
  return json.data
}

export async function getPhotoHistory(limit: number = 20, offset: number = 0): Promise<PhotoData[]> {
  return fetchData(withUser(`/history?limit=${limit}&offset=${offset}`))
}

export async function getPhotoDetail(photoId: string): Promise<PhotoData> {
  return fetchData(withUser(`/${photoId}`))
}

export function getPhotoImageUrl(photoId: string): string {
  const uid = getUserId()
  return `${BASE}/${photoId}/image?user_id=${uid}`
}

export function getPhotoThumbnailUrl(photoId: string): string {
  const uid = getUserId()
  return `${BASE}/${photoId}/thumbnail?user_id=${uid}`
}

export async function chatAboutPhoto(photoId: string, message: string): Promise<PhotoChat> {
  return fetchData(withUser(`/${photoId}/chat`), {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export async function getPhotoChats(photoId: string, limit: number = 20): Promise<PhotoChat[]> {
  return fetchData(withUser(`/${photoId}/chats?limit=${limit}`))
}

export async function sharePhotoToBridge(photoId: string, targetType: string = 'greet'): Promise<ShareResult> {
  return fetchData(withUser(`/${photoId}/share?target_type=${targetType}`), {
    method: 'POST',
  })
}
