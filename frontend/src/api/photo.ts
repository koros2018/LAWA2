/**
 * LAWA2 — 拍照理解 Agent API 封装
 */

import { apiGet, apiPost, apiUpload, getUserId } from './client'

const BASE = '/api/v2/photo'

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

export function getPhotoImageUrl(photoId: string): string {
  const uid = getUserId()
  return `${BASE}/${photoId}/image?user_id=${uid}`
}

export async function uploadPhoto(file: File, userId: string): Promise<PhotoData> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', userId)
  return apiUpload<PhotoData>(`${BASE}/upload`, formData)
}

export async function getPhotoDetail(photoId: string, userId: string): Promise<PhotoData> {
  return apiGet<PhotoData>(`${BASE}/${photoId}?user_id=${userId}`)
}

export async function chatAboutPhoto(photoId: string, userId: string, message: string): Promise<PhotoChat> {
  return apiPost<PhotoChat>(`${BASE}/${photoId}/chat`, { user_id: userId, message })
}

export async function getPhotoChats(photoId: string, userId: string): Promise<PhotoChat[]> {
  return apiGet<PhotoChat[]>(`${BASE}/${photoId}/chats?user_id=${userId}`)
}

export async function getPhotoHistory(userId: string, limit: number = 20, offset: number = 0): Promise<PhotoData[]> {
  return apiGet<PhotoData[]>(`${BASE}/list?user_id=${userId}&limit=${limit}&offset=${offset}`)
}