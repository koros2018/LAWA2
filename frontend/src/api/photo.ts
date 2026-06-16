/**
 * LAWA2 — 拍照理解 Agent API 封装（待实现）
 */
const BASE = '/api/v2/photo'

// 占位类型
export interface PhotoData {
  id: string
  image_path: string
  ai_description: string
  ai_description_en: string
  extracted_words: string[]
  scene_tags: string[]
  created_at: string
}

export interface PhotoChat {
  id: string
  role: string
  content: string
  content_en: string
  created_at: string
}