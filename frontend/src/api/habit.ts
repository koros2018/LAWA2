/**
 * LAWA2 — 习惯引擎 API 封装
 *
 * 所有后端响应格式: { status: "ok", data: ... }
 * 此层负责解包，各页面直接消费 data
 * user_id 从 session store 自动获取
 */
const BASE = '/api/v1/habit'

interface ApiResponse<T> {
  status: string
  data: T
}

function getUserId(): string {
  // 惰性加载避免循环依赖
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

// ── 数据模型 ──

export interface HabitConfig {
  trigger_time_slot: string
  info_source_prefs: string[]
  action_prefs: string[]
  reward_frequency: string
  feed_enabled: boolean
  morning_time: string
  noon_time: string
  evening_time: string
  total_xp: number
  current_streak: number
  longest_streak: number
  total_actions: number
  today_actions: number
}

export interface FeedData {
  feed_id: string
  content_type: string
  text: string
  difficulty: string
  vocab_hints: string[]
  source: string
  is_first_today: boolean
  reward: FeedReward | null
}

export interface FeedReward {
  id: string
  reward_type: string
  xp_bonus: number
  surprise_level: number
  reward_value: {
    type: string
    name: string
    icon: string
    message: string
  }
}

export interface ActionResponse {
  habit_log_id: string
  xp_earned: number
  streak_days: number
  total_habits_today: number
  reward: ActionReward | null
}

export interface ActionReward {
  id: string
  reward_type: string
  xp_bonus: number
  reward_value: {
    type: string
    name: string
    icon: string
    message: string
  }
}

export interface SummaryData {
  total_habits: number
  total_xp: number
  by_type: Record<string, number>
  streak_days: number
}

export interface GardenData {
  garden: {
    total_vocab: number
    total_assets: number
    total_milestones: number
    streak_days: number
    habit_level: number
    total_xp: number
    by_stage: Record<string, number>
  }
  new_milestones: Array<{
    code: string
    name: string
    description: string
    celebration_type: string
  }>
}

export interface RewardData {
  id: string
  reward_type: string
  xp_bonus: number
  surprise_level: number
  reward_value: {
    type: string
    name: string
    icon: string
    message: string
  }
  created_at: string
}

export interface SocialSceneData {
  vocab_id: string
  word: string
  meaning: string
  scene_example: string
  difficulty: string
  category: string
  lang_direction: string
  understanding_level: string
}

export interface SocialProgressData {
  by_category: Record<string, { understand: number; use: number; create: number }>
  total_understand: number
  total_use: number
  total_all: number
}

export interface MilestoneData {
  code: string
  name: string
  description: string
  category: string
  target_value: number
  is_achieved: boolean
  progress: number
  achieved_at: string | null
  celebration_type: string | null
  icon: string
}

export interface RecordActionBody {
  habit_code: string
  duration_seconds: number
  completion_status: string
  triggered_by: string
  feed_id?: string
}

// ── API 方法 ──

export async function getConfig(): Promise<HabitConfig> {
  return fetchData(withUser('/config'))
}

export async function getFeed(): Promise<FeedData> {
  return fetchData(withUser('/feed'))
}

export async function recordAction(body: RecordActionBody): Promise<ActionResponse> {
  return fetchData(withUser('/action'), {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getSummary(): Promise<SummaryData> {
  return fetchData(withUser('/summary'))
}

export async function getGarden(): Promise<GardenData> {
  return fetchData(withUser('/garden'))
}

export async function getRewards(): Promise<RewardData[]> {
  return fetchData(withUser('/rewards'))
}

export async function getMilestones(): Promise<MilestoneData[]> {
  return fetchData(withUser('/milestones'))
}

export interface SocialSceneData {
  vocab_id: string
  word: string
  meaning: string
  scene_example: string
  difficulty: string
  category: string
  lang_direction: string
  understanding_level: string
}

export interface SocialProgressData {
  by_category: Record<string, { understand: number; use: number; create: number }>
  total_understand: number
  total_use: number
  total_all: number
}

export async function getSocialScene(langDirection: string = 'zh'): Promise<SocialSceneData> {
  return fetchData(`${withUser('/social/adaptive')}&lang_direction=${langDirection}`)
}

export async function updateSocialLevel(vocabId: string, newLevel: string): Promise<void> {
  await fetchData(`${withUser('/social/level')}`, {
    method: 'POST',
    body: JSON.stringify({ vocab_id: vocabId, new_level: newLevel }),
  })
}

export async function getSocialProgress(): Promise<SocialProgressData> {
  return fetchData(withUser('/social/progress'))
}

export async function updateComprehension(
  feed_id: string,
  score: number,
  duration_seconds: number
): Promise<void> {
  await fetchData(withUser('/feed/comprehension'), {
    method: 'POST',
    body: JSON.stringify({ feed_id, score, duration_seconds }),
  })
}

export interface GardenReportData {
  report: string
  highlights: string[]
  week_actions: number
  week_vocab: number
  total_xp: number
  level: number
  streak: number
  can_water: boolean
  watered_today: boolean
  lang_direction: string
}

export interface HealthInsightsData {
  health_score: number
  trend: 'up' | 'down' | 'stable'
  dimensions: {
    consistency: number
    depth: number
    breadth: number
    recovery: number
  }
  recommendation: string
}

export async function getGardenReport(): Promise<GardenReportData> {
  return fetchData(withUser('/garden/report'))
}

export async function getHealthInsights(): Promise<HealthInsightsData> {
  return fetchData(withUser('/garden/health'))
}