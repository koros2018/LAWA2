/**
 * LAWA2 — 对话 API
 * v5.0.0 Phase 1
 */

import { apiGet, apiPost, apiDelete, getUserId } from './client'

export interface Conversation {
  id: number
  user_id: string
  topic: string | null
  level: number
  word_count: number
  messages?: ConversationMessage[]
  created_at: string | null
  updated_at: string | null
}

export interface ConversationMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  content_en: string | null
  order: number
  created_at: string | null
}

export interface Correction {
  id: number
  original: string
  corrected: string
  explanation: string | null
  word_diff: Record<string, unknown>
  created_at: string | null
}

export interface AIResponse {
  content: string
  content_en: string
  correction: {
    original: string
    corrected: string
    explanation: string
  } | null
}

export interface ConversationStats {
  total_conversations: number
  total_messages: number
  total_words: number
  level_distribution: Record<number, number>
}

/** 创建新对话 */
export async function createConversation(topic?: string): Promise<Conversation> {
  const userId = getUserId()
  const params = new URLSearchParams({ user_id: userId })
  if (topic) params.append('topic', topic)
  return apiGet<Conversation>(`/api/v2/conversation?${params.toString()}`)
}

/** 获取对话详情 */
export async function getConversation(id: number): Promise<Conversation> {
  return apiGet<Conversation>(`/api/v2/conversation/${id}`)
}

/** 获取用户对话列表 */
export async function getUserConversations(limit = 20): Promise<Conversation[]> {
  const userId = getUserId()
  return apiGet<Conversation[]>(`/api/v2/conversation/user/${userId}?limit=${limit}`)
}

/** 获取对话历史 */
export async function getConversationHistory(id: number, limit = 50): Promise<{ messages: ConversationMessage[]; total: number }> {
  return apiGet<{ messages: ConversationMessage[]; total: number }>(`/api/v2/conversation/${id}/history?limit=${limit}`)
}

/** 添加消息 */
export async function addMessage(conversationId: number, role: string, content: string, contentEn?: string): Promise<ConversationMessage> {
  const params = new URLSearchParams({ role, content })
  if (contentEn) params.append('content_en', contentEn)
  return apiPost<ConversationMessage>(`/api/v2/conversation/${conversationId}/messages?${params.toString()}`)
}

/** 生成 AI 回复 */
export async function generateAIResponse(
  conversationId: number,
  userMessage: string,
  level = 1,
  enableCorrection = true,
): Promise<AIResponse> {
  const params = new URLSearchParams({
    user_message: userMessage,
    level: String(level),
    enable_correction: String(enableCorrection),
  })
  return apiPost<AIResponse>(`/api/v2/conversation/${conversationId}/messages/ai?${params.toString()}`)
}

/** 删除对话 */
export async function deleteConversation(id: number): Promise<{ success: boolean }> {
  return apiDelete<{ success: boolean }>(`/api/v2/conversation/${id}`)
}

/** 获取纠错记录 */
export async function getCorrections(conversationId: number, limit = 50): Promise<{ corrections: Correction[]; total: number }> {
  return apiGet<{ corrections: Correction[]; total: number }>(`/api/v2/conversation/${conversationId}/corrections?limit=${limit}`)
}

/** 获取对话统计 */
export async function getConversationStats(): Promise<ConversationStats> {
  const userId = getUserId()
  return apiGet<ConversationStats>(`/api/v2/conversation/stats/${userId}`)
}
