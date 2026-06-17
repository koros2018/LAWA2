import { createRouter, createWebHistory } from 'vue-router'
import { session } from '@/store/session'

const routes = [
  // ── 独立页面（无底部导航） ──
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { title: 'LAWA · Login · 登录' },
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('@/views/OnboardingPage.vue'),
    meta: { title: 'LAWA · Profile · 画像', requiresAuth: true },
  },

  // ── 主 Agent：语言日常 ──
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomePage.vue'),
    meta: { title: 'LAWA · 语言日常', icon: '🧠', requiresAuth: true, agent: 'main' },
  },
  {
    path: '/feed',
    name: 'feed',
    component: () => import('@/views/FeedPage.vue'),
    meta: { title: '信息流 · Feed', icon: '📡', requiresAuth: true, agent: 'main' },
  },
  {
    path: '/garden',
    name: 'garden',
    component: () => import('@/views/GardenPage.vue'),
    meta: { title: '花园 · Garden', icon: '🌱', requiresAuth: true, agent: 'main' },
  },
  {
    path: '/bridge',
    name: 'bridge',
    component: () => import('@/views/BridgePage.vue'),
    meta: { title: '桥梁 · Bridge', icon: '🌉', requiresAuth: true, agent: 'main' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfilePage.vue'),
    meta: { title: '我的 · Profile', icon: '👤', requiresAuth: true, agent: 'main' },
  },

  // ── 事项提醒 Agent ──
  {
    path: '/reminder',
    name: 'reminder',
    component: () => import('@/views/ReminderPage.vue'),
    meta: { title: '提醒 · Reminder', icon: '📅', requiresAuth: true, agent: 'reminder' },
  },

  // ── 拍照理解 Agent ──
  {
    path: '/photo',
    name: 'photo',
    component: () => import('@/views/PhotoPage.vue'),
    meta: { title: '拍照 · Photo', icon: '📸', requiresAuth: true, agent: 'photo' },
  },

  // ── 超级管理员 Agent ──
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/AdminPage.vue'),
    meta: { title: '管理 · Admin', icon: '⚙️', requiresAuth: true, agent: 'admin' },
  },
  {
    path: '/seed-content',
    name: 'seed-content',
    component: () => import('@/views/SeedContentPage.vue'),
    meta: { title: '内容管理 · Content', icon: '📝', requiresAuth: true, agent: 'admin' },
  },
  {
    path: '/logs',
    name: 'logs',
    component: () => import('@/views/LogsPage.vue'),
    meta: { title: '日志 · Logs', icon: '📋', requiresAuth: true, agent: 'admin' },
  },
  {
    path: '/errors',
    name: 'errors',
    component: () => import('@/views/ErrorMonitorPage.vue'),
    meta: { title: '错误监控 · Errors', icon: '🔴', requiresAuth: true, agent: 'admin' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ── 路由守卫 ──
router.beforeEach((to, _from, next) => {
  const isLoggedIn = !!session.user
  const needsAuth = to.matched.some(r => r.meta.requiresAuth)
  const needsProfile = to.name === 'onboarding'
  const isAdminRoute = to.path === '/admin'
  const isUserAdmin = session.user?.isAdmin ?? false

  if (needsAuth && !isLoggedIn) {
    next('/login')
  } else if (to.name === 'login' && isLoggedIn) {
    if (session.user!.hasProfile) {
      next('/')
    } else {
      next('/onboarding')
    }
  } else if (needsProfile && !isLoggedIn) {
    next('/login')
  } else if (isAdminRoute && !isUserAdmin) {
    // 非管理员访问管理后台 → 重定向到首页
    next('/')
  } else {
    next()
  }
})

export default router