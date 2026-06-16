/**
 * LAWA2 — 拍照理解 Agent API 封装
 */
const BASE = '/api/v2/photo'

interface ApiResponse<T> {
  status: string
  data: T
}

export interface PhotoData {
  id: string
  user_id: string
  image_path: string
  original_filename: string
  file_size: number
  mime_type: string
  ai_description: string
  ai_description_en: string
  extracted_words: WordItem[]
  scene_tags: string[]
  chat_count: number
  created_at: string
}

export interface WordItem {
  word: string
  zh: string
  en: string
  example: string
}

export interface PhotoChat {
  id: string
  role: string
  content: string
  content_en: string
  created_at: string
}

export async function uploadPhoto(
  file: File,
  userId: string
): Promise<PhotoData> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', userId)

  const res = await fetch(`${BASE}/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  const json: ApiResponse<PhotoData> = await res.json()
  if (json.status !== 'ok') throw new Error(json.data as unknown as string || 'Upload failed')
  return json.data
}

export async function getPhotoImageUrl(photoId: string): string {
  return `/api/v2/photo/${photoId}/image`
}

export async function getPhotoDetail(
  photoId: string,
  userId: string
): Promise<PhotoData> {
  const res = await fetch(`${BASE}/${photoId}?user_id=${userId}`)
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`)
  const json: ApiResponse<PhotoData> = await res.json()
  if (json.status !== 'ok') throw new Error('Failed to get photo detail')
  return json.data
}

export async function chatAboutPhoto(
  photoId: string,
  userId: string,
  message: string
): Promise<PhotoChat> {
  const res = await fetch(`${BASE}/${photoId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message }),
  })
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`)
  const json: ApiResponse<PhotoChat> = await res.json()
  if (json.status !== 'ok') throw new Error('Chat failed')
  return json.data
}

export async function getPhotoChats(
  photoId: string,
  userId: string,
  limit = 20
): Promise<PhotoChat[]> {
  const res = await fetch(`${BASE}/${photoId}/chats?user_id=${userId}&limit=${limit}`)
  if (!res.ok) throw new Error(`Fetch chats failed: ${res.status}`)
  const json: ApiResponse<PhotoChat[]> = await res.json()
  if (json.status !== 'ok') throw new Error('Failed to get chats')
  return json.data
}

export async function getPhotoHistory(
  userId: string,
  limit = 20,
  offset = 0
): Promise<PhotoData[]> {
  const res = await fetch(`${BASE}/list?user_id=${userId}&limit=${limit}&offset=${offset}`)
  if (!res.ok) throw new Error(`Fetch history failed: ${res.status}`)
  const json: ApiResponse<PhotoData[]> = await res.json()
  if (json.status !== 'ok') throw new Error('Failed to get history')
  return json.data
}
