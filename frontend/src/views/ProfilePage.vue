<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getConfig, getSummary, getHealthInsights } from '@/api/habit'
import type { HabitConfig, SummaryData, HealthInsightsData } from '@/api/habit'
import { session, clearSession } from '@/store/session'

const router = useRouter()
const config = ref<HabitConfig | null>(null)
const summary = ref<SummaryData | null>(null)
const health = ref<HealthInsightsData | null>(null)
const loading = ref(true)

const user = computed(() => session.user)

const healthLabel = computed(() => {
  if (!health.value) return '—'
  const s = health.value.health_score
  if (s >= 85) return '🌿 欣欣向荣'
  if (s >= 60) return '🌱 稳步成长'
  if (s >= 30) return '💧 需要浇灌'
  return '🌰 刚刚播种'
})

const trendIcon = computed(() => {
  if (!health.value) return '➖'
  const t = health.value.trend
  if (t === 'up') return '📈'
  if (t === 'down') return '📉'
  return '➡️'
})

onMounted(async () => {
  try {
    const [c, s, h] = await Promise.all([
      getConfig(),
      getSummary(),
      getHealthInsights(),
    ])
    config.value = c
    summary.value = s
    health.value = h
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

function handleLogout() {
  clearSession()
  router.push('/login')
}
</script>

<template>
  <div class="page">
    <div class="bg-glow bg-glow-2"></div>

    <section class="hero-section profile-hero">
      <div class="avatar-circle">
        <span class="avatar-icon">👤</span>
      </div>
      <h1 class="hero-title profile-title">{{ user?.displayName || '我的' }} · Profile</h1>
      <p class="hero-subtitle" v-if="user">
        {{ user.nativeLang === 'zh' ? '中文 → 英文' : 'English → 中文' }}
      </p>
    </section>

    <!-- 统计数据 -->
    <section class="profile-stats">
      <div v-if="summary" class="stat-grid grid-2-mobile">
        <div class="card stat-block">
          <span class="stat-num">{{ summary.total_habits }}</span>
          <span class="stat-lbl">今日行动 · Actions</span>
        </div>
        <div class="card stat-block">
          <span class="stat-num">{{ summary.total_xp }}</span>
          <span class="stat-lbl">总 XP</span>
        </div>
        <div class="card stat-block">
          <span class="stat-num">{{ summary.streak_days }}</span>
          <span class="stat-lbl">连续天数 · Streak</span>
        </div>
        <div class="card stat-block">
          <span class="stat-num" v-if="config">{{ config.longest_streak }}</span>
          <span class="stat-num" v-else>—</span>
          <span class="stat-lbl">最长记录</span>
        </div>
      </div>
      <div v-else-if="loading" class="stat-grid grid-2-mobile">
        <div v-for="i in 4" :key="i" class="card skeleton" style="height: 76px;"></div>
      </div>
    </section>

    <!-- 习惯健康度洞察 -->
    <section v-if="health" class="profile-insight">
      <h2 class="section-title">🫀 习惯健康度 · Habit Health</h2>
      <div class="divider"></div>
      <div class="insight-card card">
        <div class="insight-score-row">
          <div class="insight-score">
            <span class="is-value">{{ health.health_score }}</span>
            <span class="is-label">/100</span>
          </div>
          <div class="insight-status">
            <span class="is-badge" :class="health.trend">{{ healthLabel }}</span>
            <span class="is-trend">{{ trendIcon }}</span>
          </div>
        </div>
        <div class="health-bar-wrapper">
          <div class="health-bar" :style="{
            width: health.health_score + '%',
            background: health.health_score >= 60
              ? 'linear-gradient(90deg, #7BC67E, #4CAF50)'
              : 'linear-gradient(90deg, #E8796E, #FF9800)',
          }"></div>
        </div>
        <div class="insight-dims">
          <div class="id-row" v-for="d in [
            { key: 'consistency' as const, label: '持续度', color: '#7BC67E' },
            { key: 'depth' as const, label: '深入度', color: '#4FC3F7' },
            { key: 'breadth' as const, label: '广度', color: '#BA68C8' },
            { key: 'recovery' as const, label: '恢复力', color: '#FFB74D' },
          ]" :key="d.key">
            <span class="id-label">{{ d.label }}</span>
            <div class="id-bar-bg">
              <div class="id-bar" :style="{
                width: Math.min(100, health.dimensions[d.key]) + '%',
                background: d.color,
              }"></div>
            </div>
            <span class="id-value">{{ health.dimensions[d.key] }}</span>
          </div>
        </div>
        <div class="insight-recommend">{{ health.recommendation }}</div>
      </div>
    </section>

    <!-- 用户信息 -->
    <section class="profile-prefs" v-if="user">
      <h2 class="section-title">档案 · Profile</h2>
      <div class="divider"></div>

      <div class="pref-row">
        <span class="pref-label">名字 · Name</span>
        <span class="pref-value">{{ user.displayName }}</span>
      </div>
      <div class="pref-row">
        <span class="pref-label">母语 · Native</span>
        <span class="pref-value">{{ user.nativeLang === 'zh' ? '中文' : 'English' }}</span>
      </div>
      <div class="pref-row">
        <span class="pref-label">学习目标 · Target</span>
        <span class="pref-value">{{ user.learnLang === 'en' ? 'English' : '中文' }}</span>
      </div>
      <div class="pref-row" v-if="user.interests?.length">
        <span class="pref-label">兴趣 · Interests</span>
        <span class="pref-value text-ellipsis">{{ user.interests.join(', ') }}</span>
      </div>
      <div class="pref-row" v-if="user.currentLevel">
        <span class="pref-label">水平 · Level</span>
        <span class="pref-value">{{ user.currentLevel }}</span>
      </div>
    </section>

    <!-- 偏好设置 -->
    <section class="profile-prefs" v-if="config">
      <h2 class="section-title">偏好 · Preferences</h2>
      <div class="divider"></div>

      <div class="pref-row">
        <span class="pref-label">信息源 · Sources</span>
        <span class="pref-value text-ellipsis">{{ config.info_source_prefs?.join(', ') || '默认' }}</span>
      </div>
      <div class="pref-row">
        <span class="pref-label">推送时段 · Schedule</span>
        <span class="pref-value">{{ config.morning_time }} / {{ config.noon_time }} / {{ config.evening_time }}</span>
      </div>
      <div class="pref-row">
        <span class="pref-label">推送 · Notifications</span>
        <span class="pref-value" :class="config.feed_enabled ? 'text-on' : 'text-off'">
          {{ config.feed_enabled ? '已开启' : '已关闭' }}
        </span>
      </div>
      <div class="pref-row">
        <span class="pref-label">奖励频率 · Rewards</span>
        <span class="pref-value">{{ config.reward_frequency }}</span>
      </div>
    </section>

    <!-- 关于 + 退出 -->
    <section class="profile-about">
      <h2 class="section-title">关于 · About</h2>
      <div class="divider"></div>
      <p class="about-text">
        LAWA2 — 养成式语言习惯引擎<br/>
        基于《Hooked》模型的习惯养成系统<br/>
        语言能力不是练出来的，是养出来的。
      </p>
      <div class="about-version">v2.0.0</div>

      <div class="divider"></div>
      <button class="btn btn-ghost btn-logout" @click="handleLogout">
        退出登录 · Log Out
      </button>
    </section>
  </div>
</template>

<style scoped>
.profile-hero {
  padding: var(--space-xl) 0 var(--space-lg);
}

.avatar-circle {
  width: clamp(56px, 15vw, 64px);
  height: clamp(56px, 15vw, 64px);
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-lg);
}

.avatar-icon {
  font-size: clamp(1.5rem, 5vw, 1.75rem);
}

.profile-title {
  font-size: var(--fs-title);
}

/* ── 统计 ── */
.profile-stats {
  margin-bottom: var(--space-2xl);
}

.stat-grid {
  display: grid;
  gap: var(--space-sm);
}

.stat-block {
  text-align: center;
  padding: var(--space-lg) var(--space-md);
}

@media (max-width: 374px) {
  .stat-block {
    padding: var(--space-md);
  }
}

.stat-num {
  display: block;
  font-size: var(--fs-title);
  font-weight: var(--fw-bold);
  color: var(--text-primary);
}

.stat-lbl {
  display: block;
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── 偏好/档案 ── */
.section-title {
  font-size: var(--fs-subtitle);
  font-weight: var(--fw-semibold);
  margin-bottom: var(--space-lg);
  color: var(--text-primary);
}

.pref-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--border);
  gap: var(--space-md);
}

.pref-label {
  font-size: var(--fs-body);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.pref-value {
  font-size: var(--fs-body);
  color: var(--text-primary);
  font-weight: var(--fw-medium);
  text-align: right;
  min-width: 0;
  max-width: 60%;
}

@media (max-width: 374px) {
  .pref-value {
    max-width: 55%;
    font-size: var(--fs-caption);
  }
  .pref-label {
    font-size: var(--fs-caption);
  }
}

.text-on {
  color: var(--success);
}

.text-off {
  color: var(--text-tertiary);
}

/* ── 关于 ── */
.profile-insight { margin-bottom: var(--space-2xl); }
.insight-card { border-color: rgba(147,197,253,0.25); }
.insight-score-row { display: flex; align-items: center; gap: var(--space-lg); margin-bottom: var(--space-md); }
.insight-score { display: flex; align-items: baseline; }
.is-value { font-size: var(--fs-title); font-weight: var(--fw-bold); color: var(--accent); font-variant-numeric: tabular-nums; }
.is-label { font-size: var(--fs-body); color: var(--text-tertiary); margin-left: 2px; }
.insight-status { display: flex; align-items: center; gap: var(--space-sm); }
.is-badge { font-size: var(--fs-caption); padding: 0.125rem 0.5rem; border-radius: 999px; background: rgba(74,222,128,0.15); color: #4ADE80; }
.is-badge.down { background: rgba(239,68,68,0.15); color: #EF4444; }
.is-trend { font-size: 1.25rem; }
.health-bar-wrapper { height: 6px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; margin-bottom: var(--space-md); }
.health-bar { height: 100%; border-radius: 3px; transition: width var(--duration-slow) var(--ease-out); }
.insight-dims { display: flex; flex-direction: column; gap: var(--space-sm); margin-bottom: var(--space-md); }
.id-row { display: flex; align-items: center; gap: var(--space-sm); }
.id-label { font-size: var(--fs-caption); color: var(--text-tertiary); width: 3.5em; flex-shrink: 0; }
.id-bar-bg { flex: 1; height: 4px; background: var(--bg-primary); border-radius: 2px; overflow: hidden; }
.id-bar { height: 100%; border-radius: 2px; transition: width var(--duration-slow) var(--ease-out); }
.id-value { font-size: var(--fs-caption); color: var(--text-secondary); width: 2em; text-align: right; font-variant-numeric: tabular-nums; }
.insight-recommend { font-size: var(--fs-caption); color: var(--text-tertiary); padding: var(--space-sm); background: var(--bg-primary); border-radius: var(--radius-sm); line-height: 1.5; }

.profile-about {
  margin-top: var(--space-2xl);
}

.about-text {
  font-size: var(--fs-body);
  color: var(--text-secondary);
  line-height: 1.8;
}

.about-version {
  margin-top: var(--space-md);
  font-size: var(--fs-caption);
  color: var(--text-tertiary);
  font-family: 'SF Mono', 'Cascadia Code', monospace;
}

.btn-logout {
  width: 100%;
  justify-content: center;
  color: var(--text-tertiary);
  margin-top: var(--space-md);
}
</style>