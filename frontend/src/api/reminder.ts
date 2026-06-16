/**
 * LAWA2 — 事项提醒 Agent API 封装
 */
const BASE = '/api/v2/reminder'

interface ApiResponse<T> {
  status: string
  data: T
  message?: string
}

function getUserId(): string {
  try {
    const raw = localStorage.getItem('lawa2_session')
    if (!raw) return 'test_user'
    const s = JSON.parse(raw)
    return s?.userId || 'test_user'
  } catch {
    return 'test_user'
  }
}

async function fetchData<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  const json: ApiResponse<T> = await res.json()
  if (json.status !== 'ok') throw new Error(json.message || 'API error')
  return json.data
}

// ── 类型 ──

export interface ReminderEvent {
  id: string
  title: string
  title_en: string
  event_date: string
  event_type: string
  note: string | null
  note_en: string | null
  culture_background: string | null
  culture_background_en: string | null
  is_done: boolean
  is_recurring: boolean
  recurring_rule: string | null
}

export interface GreetingData {
  zh: string
  en: string
}

// ── API ──

export async function getEvents(
  startDate?: string,
  endDate?: string,
  eventType?: string,
): Promise<ReminderEvent[]> {
  const params = new URLSearchParams({ user_id: getUserId() })
  if (startDate) params.set('start_date', startDate)
  if (endDate) params.set('end_date', endDate)
  if (eventType) params.set('event_type', eventType)
  return fetchData(`${BASE}/events?${params}`)
}

export async function getEvent(id: string): Promise<ReminderEvent> {
  return fetchData(`${BASE}/events/${id}?user_id=${getUserId()}`)
}

export async function createEvent(data: {
  title: string
  title_en?: string
  event_date: string
  event_type?: string
  note?: string
  note_en?: string
  is_recurring?: boolean
  recurring_rule?: string
}): Promise<{ id: string }> {
  return fetchData(`${BASE}/events?user_id=${getUserId()}`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateEvent(
  id: string,
  data: Partial<ReminderEvent>,
): Promise<void> {
  await fetch(`${BASE}/events/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function deleteEvent(id: string): Promise<void> {
  await fetch(`${BASE}/events/${id}`, { method: 'DELETE' })
}

export async function getUpcoming(days = 7): Promise<ReminderEvent[]> {
  return fetchData(`${BASE}/upcoming?user_id=${getUserId()}&days=${days}`)
}

export async function getToday(): Promise<ReminderEvent[]> {
  return fetchData(`${BASE}/today?user_id=${getUserId()}`)
}

export async function getHolidays(year?: number): Promise<ReminderEvent[]> {
  const params = year ? `?year=${year}` : ''
  return fetchData(`${BASE}/holidays${params}`)
}

export async function generateGreeting(
  eventId: string,
  userName = '你',
): Promise<GreetingData> {
  return fetchData(
    `${BASE}/generate-greeting?event_id=${eventId}&user_name=${encodeURIComponent(userName)}`,
    { method: 'POST' },
  )
}