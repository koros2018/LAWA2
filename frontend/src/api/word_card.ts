/**
 * Word Card API — 词汇卡片
 * 独立于 companion 系统的通用词汇卡片系统
 */
import { apiGet, apiPost, apiDelete } from './client'
import { getUserId } from './client'

function withUser(): Record<string, string> {
  return { user_id: getUserId() }
}

async function fetchData(url: string, options?: RequestInit): Promise<any> {
  const headers: Record<string, string> = {}
  if (options?.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(url, { ...options, headers })
  if (!res.ok) {
    const text = await res.text()
    let msg: string
    try { const j = JSON.parse(text); msg = j.message || j.detail || text }
    catch { msg = text }
    throw new Error(msg)
  }
  return res.json()
}

// ── 类型定义 ──

export interface WordCard {
  id: string
  user_id: string
  word: string
  lang: string
  definition: string | null
  definition_native: string | null
  part_of_speech: string | null
  phonetic: string | null
  example_sentence: string | null
  example_translation: string | null
  source: string
  source_id: string | null
  tags: string[]
  difficulty: number
  review_count: number
  review_interval_hours: number
  ease_factor: number
  last_review_at: string | null
  next_review_at: string | null
  is_mastered: boolean
  is_favorited: boolean
  created_at: string
  updated_at: string
}

export interface ReviewQueueItem extends WordCard {
  priority: number
}

export interface WordCardStats {
  total: number
  mastered: number
  learning: number
  due_today: number
  mastery_rate: number
  total_reviews: number
  source_distribution: Record<string, number>
}

// ── API 函数 ──

/** 创建词汇卡片 */
export async function createWordCard(data: {
  word: string
  lang?: string
  definition?: string
  definition_native?: string
  part_of_speech?: string
  phonetic?: string
  example_sentence?: string
  example_translation?: string
  source?: string
  tags?: string[]
  difficulty?: number
}): Promise<WordCard> {
  return fetchData('/api/v2/word-cards', {
    method: 'POST',
    body: JSON.stringify({ ...withUser(), ...data }),
  }).then(r => r.card)
}

/** 获取卡片列表 */
export async function listWordCards(params: {
  lang?: string
  mastered?: boolean | null
  favorited?: boolean | null
  source?: string
  search?: string
  page?: number
  page_size?: number
} = {}): Promise<{ items: WordCard[]; total: number; page: number; page_size: number; total_pages: number }> {
  const q = new URLSearchParams(withUser() as Record<string, string>)
  if (params.lang) q.set('lang', params.lang)
  if (params.mastered !== undefined && params.mastered !== null) q.set('mastered', String(params.mastered))
  if (params.favorited !== undefined && params.favorited !== null) q.set('favorited', String(params.favorited))
  if (params.source) q.set('source', params.source)
  if (params.search) q.set('search', params.search)
  if (params.page) q.set('page', String(params.page))
  if (params.page_size) q.set('page_size', String(params.page_size))
  return fetchData(`/api/v2/word-cards?${q.toString()}`)
}

/** 获取单张卡片 */
export async function getWordCard(cardId: string): Promise<WordCard> {
  return fetchData(`/api/v2/word-cards/${cardId}`).then(r => r.card)
}

/** 更新卡片 */
export async function updateWordCard(cardId: string, data: Partial<WordCard>): Promise<WordCard> {
  return fetchData(`/api/v2/word-cards/${cardId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }).then(r => r.card)
}

/** 删除卡片 */
export async function deleteWordCard(cardId: string): Promise<void> {
  await fetchData(`/api/v2/word-cards/${cardId}`, { method: 'DELETE' })
}

/** 提交复习 */
export async function reviewWordCard(cardId: string, quality: number): Promise<{
  id: string; word: string; quality: number; next_interval_hours: number;
  next_review_at: string | null; is_mastered: boolean; review_count: number
}> {
  return fetchData(`/api/v2/word-cards/${cardId}/review`, {
    method: 'POST',
    body: JSON.stringify({ ...withUser(), quality }),
  })
}

/** 获取待复习队列 */
export async function getReviewQueue(lang: string = 'en', limit: number = 20): Promise<{ due_count: number; queue: ReviewQueueItem[] }> {
  const q = new URLSearchParams(withUser() as Record<string, string>)
  q.set('lang', lang)
  q.set('limit', String(limit))
  return fetchData(`/api/v2/word-cards/review/queue?${q.toString()}`)
}

/** 获取统计 */
export async function getWordCardStats(lang: string = 'en'): Promise<WordCardStats> {
  const q = new URLSearchParams(withUser() as Record<string, string>)
  q.set('lang', lang)
  return fetchData(`/api/v2/word-cards/stats?${q.toString()}`)
}

/** 从 companion 同步 */
export async function syncFromCompanion(): Promise<{ synced: number }> {
  return fetchData('/api/v2/word-cards/sync-from-companion', {
    method: 'POST',
    body: JSON.stringify(withUser()),
  })
}