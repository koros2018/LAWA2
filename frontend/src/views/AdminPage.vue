<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { session } from '@/store/session'
import { handleApiError, toast } from '@/utils/error'
import {
  getAdminStats,
  getAdminUsers,
  toggleAdminUser,
  setAdminStatus,
  type SystemStats,
  type UserAdmin,
  type UsersListResponse,
  type SetAdminResponse,
} from '@/api/admin'
import ECharts from '@/components/ECharts.vue'

const activeTab = ref<'stats' | 'users'>('stats')
const stats = ref<SystemStats | null>(null)
const statsLoading = ref(true)
const users = ref<UserAdmin[]>([])
const usersTotal = ref(0)
const usersLoading = ref(false)
const searchQuery = ref('')
const userOffset = ref(0)
const USERS_PAGE_SIZE = 20
const togglingId = ref<string | null>(null)
const currentUser = ref<UserAdmin | null>(null)

// ── Chart Data ──
const trendChartData = computed(() => {
  if (!stats.value?.daily_trends?.length) return { xAxis: [], series: [] }
  const dates = stats.value.daily_trends.map(d => d.date.slice(5))
  return {
    xAxis: dates,
    series: [
      { name: '活跃用户', data: stats.value.daily_trends.map(d => d.active_users), color: '#a78bfa', area: true },
      { name: '事件数', data: stats.value.daily_trends.map(d => d.habit_events), color: '#60a5fa', area: true },
    ],
  }
})

const activityChartData = computed(() => {
  if (!stats.value) return { xAxis: [], series: [] }
  return {
    xAxis: ['今日活跃', '7日新增', '桥梁互动', '照片上传', '推送通知'],
    series: [{
      name: '数量',
      data: [
        stats.value.active_users_today,
        stats.value.new_users_7d,
        stats.value.bridge_interactions,
        stats.value.photos,
        stats.value.push_notifications,
      ],
      color: '#34d399',
    }],
  }
})

const userDistributionData = computed(() => {
  if (!stats.value) return { series: [] }
  const total = stats.value.user_count || 1
  const active = stats.value.active_users_today
  const inactive = total - active
  return {
    series: [{
      data: [
        { value: active, name: `活跃 ${active}` },
        { value: inactive, name: `非活跃 ${inactive}` },
      ],
    }],
  }
})

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await getAdminStats()
  } catch (e: any) {
    handleApiError(e, '加载统计失败 · Load failed', 'Failed to load stats')
  } finally {
    statsLoading.value = false
  }
}

async function loadUsers(append = false) {
  if (!append) userOffset.value = 0
  usersLoading.value = true
  try {
    const data = await getAdminUsers(USERS_PAGE_SIZE, userOffset.value, searchQuery.value || undefined)
    users.value = append ? [...users.value, ...data.users] : data.users
    usersTotal.value = data.total
    userOffset.value += USERS_PAGE_SIZE
  } catch (e: any) {
    handleApiError(e, '加载用户失败 · Load failed', 'Failed to load users')
  } finally {
    usersLoading.value = false
  }
}

async function toggleUser(userId: string) {
  togglingId.value = userId
  try {
    const updated = await toggleAdminUser(userId)
    const idx = users.value.findIndex(u => u.id === userId)
    if (idx >= 0) users.value[idx] = updated
  } catch (e: any) {
    handleApiError(e, '操作失败 · Toggle failed', 'Toggle failed')
  } finally {
    togglingId.value = null
  }
}

async function toggleAdmin(userId: string) {
  togglingId.value = userId
  try {
    const user = users.value.find(u => u.id === userId)
    if (!user) return
    const updated = await setAdminStatus(userId, !user.is_admin)
    const idx = users.value.findIndex(u => u.id === userId)
    if (idx >= 0) users.value[idx] = updated
  } catch (e: any) {
    handleApiError(e, '权限变更失败 · Toggle admin failed', 'Failed to toggle admin')
  } finally {
    togglingId.value = null
  }
}

function searchUsers() { loadUsers(false) }

function formatDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function safeInterests(interests: unknown): string {
  if (!interests) return '—'
  if (Array.isArray(interests)) return interests.join(', ')
  if (typeof interests === 'string') return interests
  return String(interests)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

onMounted(() => {
  // 检查当前用户权限
  if (session.user) {
    currentUser.value = {
      id: session.user.userId,
      username: session.user.username,
      display_name: session.user.displayName,
      native_lang: session.user.nativeLang,
      learn_lang: session.user.learnLang,
      current_level: session.user.currentLevel,
      habit_level: 1,
      growth_xp: 0,
      streak_days: 0,
      bridge_level: 0,
      is_active: true,
      is_admin: session.user.isAdmin ?? false,
      interests: session.user.interests,
      created_at: '',
      updated_at: '',
    }
    console.log('Current user:', currentUser.value.username, 'isAdmin:', currentUser.value.is_admin)
  }
  loadStats()
  loadUsers()
})
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
        <div class="stat-card"><span class="stat-icon">📈</span><div class="stat-info"><span class="stat-value">{{ stats.avg_events_per_user }}</span><span class="stat-label">人均事件 · Avg Events</span></div></div>
        <div class="stat-card"><span class="stat-icon">🆕</span><div class="stat-info"><span class="stat-value">{{ stats.new_users_7d }}</span><span class="stat-label">7日新增 · New Users 7d</span></div></div>
        <div class="stat-card"><span class="stat-icon">🌉</span><div class="stat-info"><span class="stat-value">{{ stats.bridge_interactions }}</span><span class="stat-label">桥梁互动 · Bridge</span></div></div>
        <div class="stat-card"><span class="stat-icon">📸</span><div class="stat-info"><span class="stat-value">{{ stats.photos }}</span><span class="stat-label">照片 · Photos</span></div></div>
        <div class="stat-card"><span class="stat-icon">🔔</span><div class="stat-info"><span class="stat-value">{{ stats.push_notifications }}</span><span class="stat-label">推送 · Push</span></div></div>
        <div class="stat-card"><span class="stat-icon">💾</span><div class="stat-info"><span class="stat-value">{{ formatSize(stats.db_size_bytes) }}</span><span class="stat-label">数据库 · Database</span></div></div>
      </div>
      
      <!-- ECharts: 7日趋势 -->
      <div class="chart-section">
        <h3 class="section-title">📈 7日趋势 · 7-Day Trends</h3>
        <ECharts type="line" :data="trendChartData" title="" />
      </div>
      
      <!-- ECharts: 活动分布 -->
      <div class="chart-section">
        <h3 class="section-title">📊 活动分布 · Activity Distribution</h3>
        <div class="charts-row">
          <div class="chart-half">
            <ECharts type="bar" :data="activityChartData" title="" />
          </div>
          <div class="chart-half">
            <ECharts type="pie" :data="userDistributionData" title="" />
          </div>
        </div>
      </div>
      
      <!-- 7日趋势（CSS 降级） -->
      <div v-if="stats && stats.daily_trends" class="trend-section css-only">
        <h3 class="section-title">📈 7日趋势 · 7-Day Trends</h3>
        <div class="trend-bars">
          <div v-for="day in stats.daily_trends" :key="day.date" class="trend-bar">
            <div class="trend-date">{{ day.date.slice(5) }}</div>
            <div class="trend-value">{{ day.active_users }}</div>
            <div class="trend-track">
              <div class="trend-fill" :style="{ width: Math.max(5, (day.active_users / (stats.active_users_today || 1) * 100)) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Top 10 用户 -->
      <div v-if="stats && stats.top_users && stats.top_users.length" class="top-users-section">
        <h3 class="section-title">🏆 Top 10 用户 · Top Users by XP</h3>
        <div class="top-users-list">
          <div v-for="(user, idx) in stats.top_users" :key="user.id" class="top-user-card">
            <span class="top-rank">{{ idx + 1 }}</span>
            <span class="top-avatar">👤</span>
            <div class="top-user-info">
              <div class="top-user-name">{{ user.display_name || user.username }}</div>
              <div class="top-user-meta">XP {{ user.growth_xp }} · {{ user.streak_days }}d · {{ user.bridge_level }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'users'" class="tab-content">
      <div class="search-bar">
        <input v-model="searchQuery" type="text" class="search-input" placeholder="🔍 搜索用户名/显示名 · Search Username/Display Name" @keyup.enter="searchUsers" />
        <button class="search-btn" @click="searchUsers">搜索 · Search</button>
      </div>
      <div class="user-count">共 {{ usersTotal }} 个用户 · Total: {{ usersTotal }} users</div>
      <div v-if="usersLoading && users.length === 0" class="loading-state"><span class="loading-spinner"></span><span>加载中... Loading...</span></div>
      <div v-else class="user-list">
        <div v-for="user in users" :key="user.id" class="user-card">
          <div class="user-header">
            <span class="user-avatar">👤</span>
            <div class="user-name"><span class="user-display">{{ user.display_name || user.username }}</span><span class="user-username">@{{ user.username }}</span></div>
            <span class="user-status" :class="{ active: user.is_active, inactive: !user.is_active }">{{ user.is_active ? 'Active' : 'Disabled' }}</span>
          </div>
          <div class="user-info">
            <div class="user-detail"><span class="detail-label">语言 · Language</span><span class="detail-value">{{ user.native_lang }} → {{ user.learn_lang }}</span></div>
            <div class="user-detail"><span class="detail-label">等级 · Level</span><span class="detail-value">{{ user.current_level || '—' }} (习惯 · Habit {{ user.habit_level }})</span></div>
            <div class="user-detail"><span class="detail-label">XP / 连续 · Streak</span><span class="detail-value">{{ user.growth_xp }} / {{ user.streak_days }}天 · {{ user.streak_days }}d</span></div>
            <div class="user-detail"><span class="detail-label">桥梁 · Bridge Level</span><span class="detail-value">{{ user.bridge_level }}</span></div>
            <div class="user-detail"><span class="detail-label">权限 · Permission</span><span class="detail-value"><span class="admin-badge" :class="{ admin: user.is_admin }">{{ user.is_admin ? '👑 Admin' : 'User' }}</span></span></div>
            <div class="user-detail"><span class="detail-label">兴趣 · Interests</span><span class="detail-value text-ellipsis">{{ safeInterests(user.interests) }}</span></div>
            <div class="user-detail"><span class="detail-label">注册时间 · Registered</span><span class="detail-value">{{ formatDate(user.created_at) }}</span></div>
          </div>
          <div class="user-actions">
            <button class="toggle-btn" :class="{ danger: user.is_active }" :disabled="togglingId === user.id" @click="toggleUser(user.id)">
              {{ togglingId === user.id ? '...' : user.is_active ? '🔴 禁用 Disable' : '🟢 启用 Enable' }}
            </button>
            <button v-if="currentUser?.is_admin" class="toggle-btn" :class="{ admin: !user.is_admin }" :disabled="togglingId === user.id" @click="toggleAdmin(user.id)">
              {{ togglingId === user.id ? '...' : user.is_admin ? '👑 取消管理员' : '👑 设为管理员' }}
            </button>
          </div>
        </div>
      </div>
      <div v-if="users.length < usersTotal" class="load-more">
        <button class="btn-ghost" :disabled="usersLoading" @click="loadUsers(true)">{{ usersLoading ? '加载中... · Loading...' : '加载更多 · Load More' }}</button>
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
.admin-badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 0.3rem; font-size: 0.7rem; font-weight: 600; }
.admin-badge.admin { background: rgba(167, 139, 250, 0.2); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.3); }
.admin-badge:not(.admin) { background: rgba(136, 136, 136, 0.15); color: #888; }
.user-info { display: grid; grid-template-columns: 1fr 1fr; gap: 0.3rem; margin-bottom: 0.5rem; }
.user-detail { display: flex; flex-direction: column; }
.detail-label { font-size: 0.6rem; color: #888; text-transform: uppercase; }
.detail-value { font-size: 0.78rem; color: #ccc; }
.text-ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-actions { display: flex; gap: 0.4rem; justify-content: flex-end; }
.toggle-btn { background: none; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; padding: 0.3rem 0.6rem; font-size: 0.75rem; cursor: pointer; color: #ccc; transition: all 0.2s; }
.toggle-btn.danger { border-color: rgba(244, 67, 54, 0.3); color: #f44336; }
.toggle-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.toggle-btn.admin { border-color: rgba(167, 139, 250, 0.4); color: #a78bfa; }
.toggle-btn.admin:hover { background: rgba(167, 139, 250, 0.1); }
.load-more { text-align: center; padding: 1rem; }
.btn-ghost { background: none; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.6rem; padding: 0.5rem 1rem; color: #a78bfa; font-size: 0.8rem; cursor: pointer; }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── 7日趋势 ── */
.trend-section { margin-top: 1.5rem; }
.chart-section { margin-top: 1.5rem; }
.charts-row { display: flex; gap: 1rem; }
.chart-half { flex: 1; }
.css-only { margin-top: 1rem; opacity: 0.7; }
.section-title { font-size: 1rem; color: #eee; margin-bottom: 0.8rem; }
.trend-bars { display: flex; flex-direction: column; gap: 0.4rem; }
.trend-bar { display: flex; align-items: center; gap: 0.5rem; }
.trend-date { font-size: 0.7rem; color: #888; width: 45px; text-align: right; }
.trend-value { font-size: 0.75rem; color: #a78bfa; width: 25px; }
.trend-track { flex: 1; height: 14px; background: rgba(255,255,255,0.05); border-radius: 7px; overflow: hidden; }
.trend-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #a78bfa); border-radius: 7px; transition: width 0.5s ease; }

/* ── Top 10 用户 ── */
.top-users-section { margin-top: 1.5rem; }
.top-users-list { display: flex; flex-direction: column; gap: 0.4rem; }
.top-user-card { display: flex; align-items: center; gap: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 0.5rem; padding: 0.5rem 0.8rem; }
.top-rank { font-size: 0.85rem; font-weight: 700; color: #c084fc; width: 20px; }
.top-avatar { font-size: 1.2rem; }
.top-user-info { flex: 1; }
.top-user-name { font-size: 0.85rem; font-weight: 600; color: #eee; }
.top-user-meta { font-size: 0.7rem; color: #888; }
</style>
