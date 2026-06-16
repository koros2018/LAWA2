<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface SystemStats {
  user_count: number
  active_users_today: number
  total_habit_events: number
  today_habit_events: number
  active_configs: number
  db_size_bytes: number
}

interface UserData {
  id: string
  username: string
  display_name: string | null
  native_lang: string
  learn_lang: string
  current_level: string | null
  habit_level: number
  growth_xp: number
  streak_days: number
  bridge_level: number
  is_active: boolean
  interests: string[]
  created_at: string
  updated_at: string
}

interface UsersResponse {
  users: UserData[]
  total: number
  limit: number
  offset: number
}

const activeTab = ref<'stats' | 'users'>('stats')
const stats = ref<SystemStats | null>(null)
const statsLoading = ref(true)
const users = ref<UserData[]>([])
const usersTotal = ref(0)
const usersLoading = ref(false)
const searchQuery = ref('')
const userOffset = ref(0)
const USERS_PAGE_SIZE = 20
const togglingId = ref<string | null>(null)

async function apiFetch<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(url, opts)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const json = await res.json()
  if (json.status !== 'ok') throw new Error(json.detail || 'API error')
  return json.data as T
}

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await apiFetch<SystemStats>('/api/v2/admin/stats')
  } catch (e: any) {
    console.error('Failed to load stats:', e)
  } finally {
    statsLoading.value = false
  }
}

async function loadUsers(append = false) {
  if (!append) userOffset.value = 0
  usersLoading.value = true
  try {
    const params = new URLSearchParams({ limit: String(USERS_PAGE_SIZE), offset: String(userOffset.value) })
    if (searchQuery.value) params.set('search', searchQuery.value)
    const data = await apiFetch<UsersResponse>(`/api/v2/admin/users?${params}`)
    users.value = append ? [...users.value, ...data.users] : data.users
    usersTotal.value = data.total
    userOffset.value += USERS_PAGE_SIZE
  } catch (e: any) {
    console.error('Failed to load users:', e)
  } finally {
    usersLoading.value = false
  }
}

async function toggleUser(userId: string) {
  togglingId.value = userId
  try {
    const updated = await apiFetch<UserData>(`/api/v2/admin/users/${userId}/toggle`, { method: 'POST' })
    const idx = users.value.findIndex(u => u.id === userId)
    if (idx >= 0) users.value[idx] = updated
  } catch (e: any) {
    console.error('Toggle failed:', e)
  } finally {
    togglingId.value = null
  }
}

function searchUsers() { loadUsers(false) }

function formatDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

onMounted(() => { loadStats(); loadUsers() })
</script>

<template>
  <div class="admin-page">
    <div class="admin-header">
      <h1>⚙️ 管理 · Admin Agent</h1>
      <p class="header-sub">User Management &amp; System Dashboard</p>
    </div>
    <div class="tab-bar">
      <button class="tab-btn" :class="{ active: activeTab === 'stats' }" @click="activeTab = 'stats'">📊 数据看板 · Dashboard</button>
      <button class="tab-btn" :class="{ active: activeTab === 'users' }" @click="activeTab = 'users'">👥 用户管理 · Users</button>
    </div>

    <section v-if="activeTab === 'stats'" class="tab-content">
      <div v-if="statsLoading" class="loading-state"><span class="loading-spinner"></span><span>加载中... Loading...</span></div>
      <div v-else-if="stats" class="stats-grid">
        <div class="stat-card"><span class="stat-icon">👥</span><div class="stat-info"><span class="stat-value">{{ stats.user_count }}</span><span class="stat-label">用户总数 · Total Users</span></div></div>
        <div class="stat-card"><span class="stat-icon">🔥</span><div class="stat-info"><span class="stat-value">{{ stats.active_users_today }}</span><span class="stat-label">今日活跃 · Active Today</span></div></div>
        <div class="stat-card"><span class="stat-icon">📝</span><div class="stat-info"><span class="stat-value">{{ stats.total_habit_events }}</span><span class="stat-label">总事件 · Total Events</span></div></div>
        <div class="stat-card"><span class="stat-icon">📅</span><div class="stat-info"><span class="stat-value">{{ stats.today_habit_events }}</span><span class="stat-label">今日事件 · Today's Events</span></div></div>
        <div class="stat-card"><span class="stat-icon">⚙️</span><div class="stat-info"><span class="stat-value">{{ stats.active_configs }}</span><span class="stat-label">活跃配置 · Active Configs</span></div></div>
        <div class="stat-card"><span class="stat-icon">💾</span><div class="stat-info"><span class="stat-value">{{ formatSize(stats.db_size_bytes) }}</span><span class="stat-label">数据库 · Database</span></div></div>
      </div>
    </section>

    <section v-if="activeTab === 'users'" class="tab-content">
      <div class="search-bar">
        <input v-model="searchQuery" type="text" class="search-input" placeholder="🔍 搜索用户名/显示名 · Search" @keyup.enter="searchUsers" />
        <button class="search-btn" @click="searchUsers">搜索 · Search</button>
      </div>
      <div class="user-count">共 {{ usersTotal }} 个用户 · Total</div>
      <div v-if="usersLoading && users.length === 0" class="loading-state"><span class="loading-spinner"></span><span>加载中... Loading...</span></div>
      <div v-else class="user-list">
        <div v-for="user in users" :key="user.id" class="user-card">
          <div class="user-header">
            <span class="user-avatar">👤</span>
            <div class="user-name"><span class="user-display">{{ user.display_name || user.username }}</span><span class="user-username">@{{ user.username }}</span></div>
            <span class="user-status" :class="{ active: user.is_active, inactive: !user.is_active }">{{ user.is_active ? 'Active' : 'Disabled' }}</span>
          </div>
          <div class="user-info">
            <div class="user-detail"><span class="detail-label">语言 Lang</span><span class="detail-value">{{ user.native_lang }} → {{ user.learn_lang }}</span></div>
            <div class="user-detail"><span class="detail-label">等级 Level</span><span class="detail-value">{{ user.current_level || '—' }} (习惯 {{ user.habit_level }})</span></div>
            <div class="user-detail"><span class="detail-label">XP / 连续</span><span class="detail-value">{{ user.growth_xp }} / {{ user.streak_days }}天</span></div>
            <div class="user-detail"><span class="detail-label">桥梁 Level</span><span class="detail-value">{{ user.bridge_level }}</span></div>
            <div class="user-detail"><span class="detail-label">兴趣 Interests</span><span class="detail-value text-ellipsis">{{ user.interests?.length ? user.interests.join(', ') : '—' }}</span></div>
            <div class="user-detail"><span class="detail-label">注册时间</span><span class="detail-value">{{ formatDate(user.created_at) }}</span></div>
          </div>
          <div class="user-actions">
            <button class="toggle-btn" :class="{ danger: user.is_active }" :disabled="togglingId === user.id" @click="toggleUser(user.id)">
              {{ togglingId === user.id ? '...' : user.is_active ? '🔴 禁用 Disable' : '🟢 启用 Enable' }}
            </button>
          </div>
        </div>
      </div>
      <div v-if="users.length < usersTotal" class="load-more">
        <button class="btn-ghost" :disabled="usersLoading" @click="loadUsers(true)">{{ usersLoading ? '加载中...' : '加载更多 · Load More' }}</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-page { min-height: 100dvh; background: linear-gradient(180deg, #0a0a1a 0%, #0f0f2a 100%); padding: 1rem; padding-bottom: calc(1rem + env(safe-area-inset-bottom, 0px) + 5rem); }
.admin-header { text-align: center; padding: 1.5rem 0 1rem; }
.admin-header h1 { font-size: 1.3rem; font-weight: 600; color: #eee; margin-bottom: 0.3rem; }
.header-sub { font-size: 0.8rem; color: #888; font-style: italic; }
.tab-bar { display: flex; gap: 0.3rem; margin-bottom: 1rem; background: rgba(255,255,255,0.03); border-radius: 0.75rem; padding: 0.25rem; }
.tab-btn { flex: 1; padding: 0.5rem 0.4rem; border: none; border-radius: 0.6rem; background: transparent; color: #888; font-size: 0.75rem; cursor: pointer; transition: all 0.2s; }
.tab-btn.active { background: rgba(167, 139, 250, 0.15); color: #a78bfa; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.stat-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 0.75rem; padding: 0.8rem; display: flex; align-items: center; gap: 0.6rem; }
.stat-icon { font-size: 1.5rem; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 1.2rem; font-weight: 700; color: #eee; }
.stat-label { font-size: 0.65rem; color: #888; }
.loading-state { display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 2rem; color: #888; font-size: 0.9rem; }
.loading-spinner { width: 1rem; height: 1rem; border: 2px solid rgba(167, 139, 250, 0.2); border-top-color: #a78bfa; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.search-bar { display: flex; gap: 0.4rem; margin-bottom: 0.5rem; }
.search-input { flex: 1; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.6rem; padding: 0.5rem 0.75rem; color: white; font-size: 0.8rem; outline: none; }
.search-input:focus { border-color: rgba(167, 139, 250, 0.4); }
.search-input::placeholder { color: #555; }
.search-btn { background: linear-gradient(135deg, #7c3aed, #6366f1); color: white; border: none; border-radius: 0.6rem; padding: 0.5rem 0.8rem; font-size: 0.8rem; cursor: pointer; white-space: nowrap; }
.user-count { font-size: 0.7rem; color: #888; margin-bottom: 0.5rem; }
.user-list { display: flex; flex-direction: column; gap: 0.5rem; }
.user-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 0.75rem; padding: 0.8rem; }
.user-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.user-avatar { font-size: 1.5rem; }
.user-name { flex: 1; display: flex; flex-direction: column; }
.user-display { font-size: 0.9rem; font-weight: 600; color: #eee; }
.user-username { font-size: 0.7rem; color: #888; }
.user-status { font-size: 0.65rem; padding: 0.15rem 0.4rem; border-radius: 0.4rem; font-weight: 600; }
.user-status.active { background: rgba(76, 175, 80, 0.15); color: #4CAF50; }
.user-status.inactive { background: rgba(244, 67, 54, 0.15); color: #f44336; }
.user-info { display: grid; grid-template-columns: 1fr 1fr; gap: 0.3rem; margin-bottom: 0.5rem; }
.user-detail { display: flex; flex-direction: column; }
.detail-label { font-size: 0.6rem; color: #888; text-transform: uppercase; }
.detail-value { font-size: 0.78rem; color: #ccc; }
.text-ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-actions { display: flex; gap: 0.4rem; justify-content: flex-end; }
.toggle-btn { background: none; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; padding: 0.3rem 0.6rem; font-size: 0.75rem; cursor: pointer; color: #ccc; transition: all 0.2s; }
.toggle-btn.danger { border-color: rgba(244, 67, 54, 0.3); color: #f44336; }
.toggle-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.load-more { text-align: center; padding: 1rem; }
.btn-ghost { background: none; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.6rem; padding: 0.5rem 1rem; color: #a78bfa; font-size: 0.8rem; cursor: pointer; }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
