/**
 * 双向桥梁 API 封装
 * Lv.1 你好桥 / Lv.2 点赞桥 / Lv.3 梗桥
 */
const BRIDGE_BASE = '/api/v2/bridge'

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

async function bridgeFetch<T>(url: string, init?: RequestInit): Promise<T> {
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
  return `${BRIDGE_BASE}${path}${sep}user_id=${encodeURIComponent(uid)}`
}

// ── 数据模型 ──

export interface BridgePartner {
  partner_id: string
  partner_name: string
  native_lang: string
  learn_lang: string
  bio: string
  bridge_level: number
}

export interface BridgeGreeting {
  interaction_id: string
  partner_name: string
  greeting: string
  translation: string
  context: string
  direction: string
  created_at: string
}

export interface BridgeReply {
  status: string
  your_reply: string
  polished: string
  partner_reply: string
  xp_earned: number
}

export interface BridgeLikePrompt {
  interaction_id: string
  partner_name: string
  message: string
  translation: string
  context: string
  level: number
  direction: string
  created_at: string
}

export interface BridgeTeachPrompt {
  interaction_id: string
  partner_name: string
  message: string
  translation: string
  context: string
  level: number
  direction: string
  created_at: string
}

export interface BridgeTeachResult {
  status: string
  word: string
  meaning: string
  partner_curious: string
  partner_try_use: string
  partner_thanks: string
  xp_earned: number
}

export interface BridgeHistory {
  id: string
  level: number
  direction: string
  learn_text: string
  native_text: string
  polished_text: string | null
  partner_reply: string | null
  xp_earned: number
  created_at: string
}

export interface BridgeProgress {
  current_level: number
  total_interactions: number
  total_xp: number
  next_level_at: string
  levels: Array<{
    level: number
    name: string
    unlocked: boolean
    done: boolean
  }>
}

// ── API 方法 ──

export async function getBridgePartner(): Promise<BridgePartner> {
  return bridgeFetch(withUser('/partner'))
}

export async function getBridgeGreeting(): Promise<BridgeGreeting> {
  return bridgeFetch(withUser('/greeting'))
}

export async function replyBridgeGreeting(interactionId: string, replyText: string): Promise<BridgeReply> {
  return bridgeFetch(withUser('/reply'), {
    method: 'POST',
    body: JSON.stringify({ interaction_id: interactionId, reply_text: replyText }),
  })
}

export async function getBridgeHistory(limit = 10): Promise<BridgeHistory[]> {
  return bridgeFetch(withUser(`/history?limit=${limit}`))
}

export async function getBridgeProgress(): Promise<BridgeProgress> {
  return bridgeFetch(withUser('/progress'))
}

// ── Lv.2 点赞桥 ──

export async function getBridgeLikePrompt(): Promise<BridgeLikePrompt> {
  return bridgeFetch(withUser('/like'))
}

export async function replyBridgeLike(interactionId: string, replyText: string): Promise<BridgeReply> {
  return bridgeFetch(withUser('/like'), {
    method: 'POST',
    body: JSON.stringify({ interaction_id: interactionId, reply_text: replyText }),
  })
}

// ── Lv.3 梗桥 ──

export async function getBridgeTeachPrompt(): Promise<BridgeTeachPrompt> {
  return bridgeFetch(withUser('/teach'))
}

export async function teachBridgeWord(
  interactionId: string, word: string, meaning: string, example = ''
): Promise<BridgeTeachResult> {
  return bridgeFetch(withUser('/teach'), {
    method: 'POST',
    body: JSON.stringify({ interaction_id: interactionId, word, meaning, example }),
  })
}