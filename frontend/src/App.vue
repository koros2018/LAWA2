<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { session } from '@/store/session'

const router = useRouter()
const route = useRoute()

interface AgentItem {
  key: string
  label: string
  labelEn: string
  icon: string
  route: string
}

const agents = computed(() => {
  const base: AgentItem[] = [
    { key: 'main', label: '语言日常', labelEn: 'Daily', icon: '🧠', route: '/' },
    { key: 'reminder', label: '事项提醒', labelEn: 'Reminder', icon: '📅', route: '/reminder' },
    { key: 'photo', label: '拍照理解', labelEn: 'Photo', icon: '📸', route: '/photo' },
  ]
  // 仅管理员可见管理后台 · Admin tab only visible to admin users
  if (session.user?.isAdmin) {
    base.push({ key: 'admin', label: '管理', labelEn: 'Admin', icon: '⚙️', route: '/admin' })
  }
  return base
})

// 当前激活的 Agent
const currentAgent = computed(() => {
  const meta = route.meta as Record<string, any> | undefined
  return meta?.agent ?? 'main'
})

// 主 Agent 内部子导航
const mainSubItems = [
  { name: 'home', label: '首页', labelEn: 'Home', icon: '🌿' },
  { name: 'feed', label: '信息流', labelEn: 'Feed', icon: '📡' },
  { name: 'bridge', label: '桥梁', labelEn: 'Bridge', icon: '🌉' },
  { name: 'garden', label: '花园', labelEn: 'Garden', icon: '🌱' },
  { name: 'profile', label: '我的', labelEn: 'Profile', icon: '👤' },
]

// 显示底部导航（已登录 + 已画像 + 非登录/画像页）
const showNav = computed(() => {
  return session.user && session.user.hasProfile && route.name !== 'login' && route.name !== 'onboarding'
})

// 显示主 Agent 子导航（当前在主 Agent 下）
const showMainSubNav = computed(() => {
  return showNav.value && currentAgent.value === 'main'
})

function navigateAgent(agent: AgentItem) {
  router.push(agent.route)
}

function navigateSub(name: string) {
  router.push({ name })
}

function isActive(name: string) {
  return route.name === name
}
</script>

<template>
  <div class="app-shell">
    <router-view />

    <!-- Agent 选择底部导航 -->
    <nav v-if="showNav" class="agent-nav">
      <button
        v-for="agent in agents"
        :key="agent.key"
        class="agent-nav-item"
        :class="{ active: currentAgent === agent.key }"
        @click="navigateAgent(agent)"
      >
        <span class="agent-nav-icon">{{ agent.icon }}</span>
        <span class="agent-nav-label">{{ agent.label }}</span>
        <span class="agent-nav-label-en">{{ agent.labelEn }}</span>
      </button>
    </nav>

    <!-- 主 Agent 内部子导航 -->
    <nav v-if="showMainSubNav" class="sub-nav">
      <button
        v-for="item in mainSubItems"
        :key="item.name"
        class="sub-nav-item"
        :class="{ active: isActive(item.name) }"
        @click="navigateSub(item.name)"
      >
        <span class="sub-nav-icon">{{ item.icon }}</span>
        <span class="sub-nav-label">{{ item.label }}</span>
        <span class="sub-nav-label-en">{{ item.labelEn }}</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* ── Agent 选择器（底部） ── */
.agent-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 0.35rem 0.5rem;
  padding-bottom: calc(0.35rem + env(safe-area-inset-bottom, 0px));
  background: rgba(15, 15, 30, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  z-index: 100;
}

.agent-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  padding: 0.25rem 0.5rem;
  background: none;
  border: none;
  color: var(--text-muted, #888);
  cursor: pointer;
  transition: color 0.2s;
  min-width: 3.5rem;
}

.agent-nav-item.active {
  color: var(--accent, #a78bfa);
}

.agent-nav-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.agent-nav-label {
  font-size: 0.6rem;
  line-height: 1;
}

.agent-nav-label-en {
  font-size: 0.5rem;
  line-height: 1;
  opacity: 0.6;
}

/* ── 主 Agent 内部子导航 ── */
.sub-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 0.4rem 0.5rem;
  padding-top: calc(0.4rem + env(safe-area-inset-top, 0px));
  background: rgba(15, 15, 30, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  z-index: 100;
}

.sub-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
  padding: 0.2rem 0.4rem;
  background: none;
  border: none;
  color: var(--text-muted, #888);
  cursor: pointer;
  transition: color 0.2s;
  font-size: 0.65rem;
}

.sub-nav-item.active {
  color: var(--accent, #a78bfa);
}

.sub-nav-icon {
  font-size: 1rem;
  line-height: 1;
}

.sub-nav-label {
  font-size: 0.55rem;
  line-height: 1;
}

.sub-nav-label-en {
  font-size: 0.5rem;
  line-height: 1;
  opacity: 0.6;
}
</style>
