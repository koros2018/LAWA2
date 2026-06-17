/**
 * LAWA2 — 提醒 Agent API 封装 (/agent/reminder)
 */
const BASE = '/agent/reminder'

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

export async function getReminderAgentHealth(): Promise<AgentHealth> {
  const res = await fetch(`${BASE}/health`, { headers: { 'Content-Type': 'application/json' } })
  const json = await res.json()
  return json
}

// ── 数据模型 ──

export interface ReminderEvent {
  id: string
  user_id: string
  title: string
  title_en?: string
  event_date: string
  event_type: string
  note?: string
  note_en?: string
  is_done: boolean
  is_recurring: boolean
  recurring_rule?: string
  created_at: string
  updated_at: string
}

export interface Holiday {
  id: string
  name: string
  name_en: string
  month: number
  day: number
  description: string
  description_en?: string
  culture_background: string
  culture_background_en: string
}

export interface GreetingResult {
  zh: string
  en: string
}

export interface EventCreateBody {
  title: string
  title_en?: string
  event_date: string
  event_type?: string
  note?: string
  note_en?: string
  is_recurring?: boolean
  recurring_rule?: string
}

export interface EventUpdateBody {
  title?: string
  title_en?: string
  event_date?: string
  event_type?: string
  note?: string
  note_en?: string
  is_done?: boolean
  is_recurring?: boolean
  recurring_rule?: string
}

// ── API 方法 ──

export async function getEvents(
  startDate?: string,
  endDate?: string,
  eventType?: string,
  limit: number = 50
): Promise<ReminderEvent[]> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)
  if (eventType) params.append('event_type', eventType)
  return fetchData(withUser(`/events?${params}`))
}

export async function getEvent(eventId: string): Promise<ReminderEvent> {
  return fetchData(withUser(`/events/${eventId}`))
}

export async function createEvent(body: EventCreateBody): Promise<ReminderEvent> {
  return fetchData(withUser('/events'), {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function updateEvent(eventId: string, body: EventUpdateBody): Promise<ReminderEvent> {
  return fetchData(withUser(`/events/${eventId}`), {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export async function deleteEvent(eventId: string): Promise<{ status: string }> {
  return fetchData(withUser(`/events/${eventId}`), { method: 'DELETE' })
}

export async function getHolidays(year?: number): Promise<Holiday[]> {
  const param = year ? `?year=${year}` : ''
  return fetchData(withUser(`/holidays${param}`))
}

export async function getTodayHolidays(): Promise<Holiday[]> {
  return fetchData(withUser('/holidays/today'))
}

export async function generateGreeting(eventId: string, userName: string = '你'): Promise<GreetingResult> {
  return fetchData(withUser('/generate-greeting'), {
    method: 'POST',
    body: JSON.stringify({ event_id: eventId, user_name: userName }),
  })
}
