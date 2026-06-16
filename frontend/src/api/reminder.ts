/**
 * LAWA2 — 事项提醒 Agent API 封装
 */

import { apiGet, apiPost, apiPut, apiDelete, getUserId } from './client'

const BASE = '/api/v2/reminder'

export interface ReminderEvent {
  id: string
  user_id: string
  title: string
  description: string
  date: string
  event_type: 'user' | 'holiday'
  is_recurring: boolean
  created_at: string
  updated_at: string
}

export interface Holiday {
  date: string
  name_zh: string
  name_en: string
  type: string
}

export interface GreetingResult {
  greeting_zh: string
  greeting_en: string
}

// ── 事件 CRUD ──

export async function getEvents(userId: string, startDate?: string, endDate?: string): Promise<ReminderEvent[]> {
  const params = new URLSearchParams({ user_id: userId })
  if (startDate) params.set('start_date', startDate)
  if (endDate) params.set('end_date', endDate)
  return apiGet<ReminderEvent[]>(`${BASE}/events?${params}`)
}

export async function createEvent(userId: string, data: { title: string; description: string; date: string }): Promise<ReminderEvent> {
  return apiPost<ReminderEvent>(`${BASE}/events?user_id=${userId}`, data)
}

export async function updateEvent(eventId: string, data: { title?: string; description?: string; date?: string }): Promise<ReminderEvent> {
  return apiPut<ReminderEvent>(`${BASE}/events/${eventId}`, data)
}

export async function deleteEvent(eventId: string): Promise<void> {
  await apiDelete<void>(`${BASE}/events/${eventId}`)
}

export async function getTodayEvents(userId: string): Promise<ReminderEvent[]> {
  return apiGet<ReminderEvent[]>(`${BASE}/today?user_id=${userId}`)
}

export async function getUpcomingEvents(userId: string, days: number = 7): Promise<ReminderEvent[]> {
  return apiGet<ReminderEvent[]>(`${BASE}/upcoming?user_id=${userId}&days=${days}`)
}

export async function getHolidays(year: number): Promise<Holiday[]> {
  return apiGet<Holiday[]>(`${BASE}/holidays?year=${year}`)
}

export async function generateGreeting(eventId: string, userName: string): Promise<GreetingResult> {
  return apiPost<GreetingResult>(`${BASE}/generate-greeting?event_id=${eventId}&user_name=${encodeURIComponent(userName)}`)
}

export async function seedHolidays(): Promise<void> {
  await apiPost<void>(`${BASE}/seed-holidays`)
}