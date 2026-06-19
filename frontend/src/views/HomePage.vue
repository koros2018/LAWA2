<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSummary, getConfig, getFeed, recordAction } from '@/api/agent_main'
import type { SummaryData, HabitConfig, FeedData, ActionResponse } from '@/api/agent_main'
import { session, updateProfile } from '@/store/session'
import { handleApiError, toast } from '@/utils/error'

const summary = ref<SummaryData | null>(null)
const config = ref<HabitConfig | null>(null)
const feed = ref<FeedData | null>(null)
const loading = ref(true)
const actionResult = ref<ActionResponse | null>(null)
const showGuide = ref(session.user?.isNewUser ?? false)
const loadError = ref<string | null>(null)

onMounted(async () => {
  try {
    const [s, c, f] = await Promise.all([
      getSummary(),
      getConfig(),
      getFeed(),
    ])
    summary.value = s
    config.value = c
    feed.value = f
  } catch (e) {
    loadError.value = handleApiError(e, '加载失败 · Load failed', 'Failed to load data')
  } finally {
    loading.value = false
  }
})

function dismissGuide() {
  showGuide.value = false
}

async function quickAction(code: string) {
  try {
    actionResult.value = await recordAction({
      habit_code: code,
      duration_seconds: 15,
      completion_status: 'completed',
      triggered_by: 'manual',
      feed_id: feed.value?.feed_id,
    })
    summary.value = await getSummary()
    setTimeout(() => { actionResult.value = null }, 3000)
  } catch (e) {
    handleApiError(e, '操作失败 · Action failed', 'Action failed')
  }
}

const quickActions = [
  { code: 'read_one_post', label: '读一条 · Read', icon: '📰' },
  { code: 'look_up_one', label: '查个词 · Look Up', icon: '🔍' },
  { code: 'say_one_thing', label: '跟读 · Repeat', icon: '🎤' },
]
</script>

<template>
  <div class="page">
    <div class="bg-glow bg-glow-1"></div>
    <div class="bg-glow bg-glow-2"></div>

    <section class="hero-section">
      <div class="hero-label" v-if="!loading">
        <span class="badge" v-if="config">
          🔥 连续 {{ config.current_streak }} 天 · {{ config.current_streak }}-day streak · {{ config.current_streak }}-day streak
        </span>
      </div>
      <h1 class="hero-title">你的语言正在生长<br/><span class="hero-subtitle-en">Your Language, Growing Naturally</span></h1>
      <p class="hero-subtitle">
        语言能力不是练出来的，是养出来的。<br/>
        每一天的信息流，都是浇灌。<br/>
        Your language grows with daily nourishment.<br/>
        <span class="hero-subtitle-en">Language grows with daily nourishment.</span>
      </p>
    </section>

    <!-- 今日状态 -->
    <section class="stats-row">
      <template v-if="summary">
        <div class="stat-card">
          <span class="stat-value">{{ summary.total_xp }}</span>
          <span class="stat-label">总 XP · Total XP</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ summary.total_habits }}</span>
          <span class="stat-label">今日行为 · Habits</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ summary.streak_days }}</span>
          <span class="stat-label">连续天数 · Streak</span>
        </div>
      </template>
      <template v-else-if="loadError">
        <div class="error-state">
          <p class="error-icon">⚠️</p>
          <p class="error-title">加载失败 · Load failed</p>
          <p class="error-desc">{{ loadError }}</p>
          <button class="btn btn-primary" @click="location.reload()">
            🔄 重试 · Retry
          </button>
        </div>
      </template>
      <div v-else class="stat-card" v-for="i in 3" :key="i">
        <div class="skeleton stat-skel"></div>
        <div class="skeleton stat-skel-label"></div>
      </div>
    </section>

    <!-- 快速行动 -->
    <section class="quick-actions">
      <h2 class="section-title">来点微行动 · Micro Actions</h2>
      <div class="action-grid">
        <button
          v-for="act in quickActions"
          :key="act.code"
          class="action-btn"
          @click="quickAction(act.code)"
          :disabled="!!actionResult"
        >
          <span class="action-icon">{{ act.icon }}</span>
          <span class="action-label">{{ act.label }}</span>
        </button>
      </div>

      <Transition name="fade">
        <div v-if="actionResult" class="action-feedback card">
          <span class="feedback-icon">✨</span>
          <span>+{{ actionResult.xp_earned }} XP 经验 · Experience</span>
          <span v-if="actionResult.reward" class="reward-text">
            🎁 {{ actionResult.reward.reward_value?.name || '奖励' }}
          </span>
        </div>
      </Transition>
    </section>

    <section class="feed-preview" v-if="feed">
      <h2 class="section-title">今日信息流 · Today's Feed</h2>
      <p class="section-subtitle">Daily content curated for your level</p>
      <div class="divider"></div>
      <div class="feed-item">
        <div class="feed-meta">
          <span class="badge">{{ feed.content_type }}</span>
          <span class="feed-diff">{{ feed.difficulty }}</span>
        </div>
        <p class="feed-text">{{ feed.text }}</p>
        <div class="feed-hints" v-if="feed.vocab_hints?.length">
          <span class="hint-label">生词 · Vocab</span>
          <span class="hint-word" v-for="w in feed.vocab_hints" :key="w">{{ w }}</span>
        </div>
      </div>
      <router-link to="/feed" class="btn btn-ghost feed-more">
        查看更多 · See More →
      </router-link>
    </section>

    <!-- 首次引导 overlay -->
    <Transition name="fade">
      <div v-if="showGuide" class="guide-overlay" @click="dismissGuide">
        <div class="guide-card" @click.stop>
          <div class="guide-close" @click="dismissGuide">✕</div>
          <div class="guide-icon">🌿</div>
          <h2 class="guide-title">欢迎来到你的语言花园<br/><span class="guide-title-en">Welcome to Your Language Garden</span></h2>
          <div class="guide-steps">
            <div class="guide-step">
              <span class="guide-step-num">1</span>
              <span class="guide-step-text">点击「📰 读一条」开始今日练习</span>
              <span class="guide-step-text-en">Tap "Read" to start today's practice</span>
            </div>
            <div class="guide-step">
              <span class="guide-step-num">2</span>
              <span class="guide-step-text">查看下方的信息流，学习新词汇</span>
              <span class="guide-step-text-en">Browse the feed below to learn new words</span>
            </div>
            <div class="guide-step">
              <span class="guide-step-num">3</span>
              <span class="guide-step-text">在「花园」查看你的成长轨迹</span>
              <span class="guide-step-text-en">Visit "Garden" to see your progress</span>
            </div>
          </div>
          <button class="btn-guide-start" @click="dismissGuide">
            开始探索 · Let's Go →
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ── Hero ── */
.hero-label {
  margin-bottom: var(--space-lg);
}

/* ── 统计行 ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
  margin-bottom: var(--space-2xl);
}

@media (max-width: 374px) {
  .stats-row {
    gap: 0.375rem;
  }
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-lg) var(--space-md);
  text-align: center;
}

@media (max-width: 374px) {
  .stat-card {
    padding: var(--space-md) var(--space-sm);
  }
}

.stat-value {
  display: block;
  font-size: var(--fs-title);
  font-weight: var(--fw-bold);
  color: var(--text-primary);
  line-height: 1.1;
}

.stat-label {
  display: block;
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.hero-subtitle-en {
  font-size: var(--fs-caption);
  color: var(--text-tertiary);
  font-style: italic;
  margin-bottom: var(--space-sm);
}

.section-subtitle {
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  margin-top: calc(-1 * var(--space-lg));
  margin-bottom: var(--space-lg);
}

.stat-skel {
  height: 1.5rem;
  width: 60%;
  margin: 0 auto 0.5rem;
}

.stat-skel-label {
  height: 0.75rem;
  width: 40%;
  margin: 0 auto;
}

/* ── 章节标题 ── */
.section-title {
  font-size: var(--fs-subtitle);
  font-weight: var(--fw-semibold);
  margin-bottom: var(--space-lg);
  color: var(--text-primary);
}

/* ── 快速行动 ── */
.quick-actions {
  margin-bottom: var(--space-2xl);
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
}

@media (max-width: 374px) {
  .action-grid {
    gap: 0.375rem;
  }
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-lg) var(--space-md);
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
  color: var(--text-primary);
  font-family: inherit;
  -webkit-tap-highlight-color: transparent;
  min-height: 72px;
}

@media (max-width: 374px) {
  .action-btn {
    min-height: 64px;
    padding: var(--space-md) var(--space-sm);
  }
}

.action-btn:hover:not(:disabled) {
  border-color: var(--accent);
  background: var(--accent-glow);
  transform: translateY(-2px);
}
.action-btn:active:not(:disabled) {
  transform: translateY(0);
}
.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  font-size: clamp(1.5rem, 5vw, 1.75rem);
}

.action-label {
  font-size: var(--fs-small);
  font-weight: var(--fw-medium);
  color: var(--text-secondary);
}

.action-feedback {
  margin-top: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  font-size: var(--fs-caption);
  color: var(--success);
  flex-wrap: wrap;
}

@media (max-width: 374px) {
  .action-feedback {
    gap: var(--space-sm);
  }
}

.feedback-icon {
  font-size: 1.25rem;
  animation: sparkle 1s ease-in-out infinite;
}
@keyframes sparkle {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

.reward-text {
  color: var(--warning);
  font-weight: var(--fw-medium);
}

/* ── 信息流预览 ── */
.feed-preview {
  margin-bottom: var(--space-2xl);
}

.feed-item {
  padding: var(--space-md) 0;
}

.feed-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  flex-wrap: wrap;
}

.feed-diff {
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
}

.feed-text {
  font-size: var(--fs-body);
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
  word-break: break-word;
}

.feed-hints {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.hint-label {
  font-size: var(--fs-small);
  color: var(--text-tertiary);
}

.hint-word {
  font-size: var(--fs-small);
  color: var(--accent);
  background: var(--accent-glow);
  padding: 2px 8px;
  border-radius: 4px;
}

.feed-more {
  margin-top: var(--space-md);
  width: 100%;
  justify-content: center;
}

/* ── 首次引导 overlay ── */
.guide-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: var(--space-xl);
}

.guide-card {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-2xl);
  max-width: 360px;
  width: 100%;
  position: relative;
  text-align: center;
  animation: cardIn 0.3s ease-out;
}

@keyframes cardIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.guide-close {
  position: absolute;
  top: var(--space-md);
  right: var(--space-md);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.guide-close:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

/* ── 错误状态 ── */
.error-state {
  text-align: center;
  padding: var(--space-3xl) 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  color: var(--text-tertiary);
}

.error-icon {
  font-size: 3rem;
  animation: shake 0.5s ease-in-out;
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
}
.error-title {
  font-size: var(--fs-title);
  font-weight: var(--fw-bold);
  color: #f87171;
}
.error-desc {
  font-size: var(--fs-small);
  color: var(--text-muted);
  max-width: 200px;
}

/* ── Toast ── */
.toast-container {
  position: fixed;
  top: var(--space-lg);
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  pointer-events: none;
}

.toast {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-md) var(--space-lg);
  font-size: var(--fs-small);
  color: var(--text-primary);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  pointer-events: auto;
  min-width: 200px;
  max-width: 320px;
  text-align: center;
}

.toast.error {
  border-color: rgba(239, 68, 68, 0.5);
  color: #fca5a5;
}

.toast.success {
  border-color: rgba(34, 197, 94, 0.5);
  color: #86efac;
}

.toast.warning {
  border-color: rgba(251, 191, 36, 0.5);
  color: #fde047;
}

.toast.info {
  border-color: rgba(96, 165, 250, 0.5);
  color: #93c5fd;
}

.guide-icon {
  font-size: 2.5rem;
  margin-bottom: var(--space-lg);
}

.guide-title {
  font-size: var(--fs-subtitle);
  font-weight: var(--fw-bold);
  color: var(--text-primary);
  margin-bottom: var(--space-xl);
}

.guide-title-en {
  font-size: var(--fs-caption);
  color: var(--text-tertiary);
  font-weight: var(--fw-normal);
  display: block;
  margin-top: var(--space-xs);
}

.guide-steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
  text-align: left;
}

.guide-step {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
}

.guide-step-num {
  width: 24px;
  height: 24px;
  background: var(--accent-glow);
  color: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-small);
  font-weight: var(--fw-bold);
  flex-shrink: 0;
}

.guide-step-text {
  display: block;
  font-size: var(--fs-caption);
  color: var(--text-primary);
  line-height: 1.4;
}

.guide-step-text-en {
  display: block;
  font-size: var(--fs-small);
  color: var(--text-tertiary);
}

.btn-guide-start {
  width: 100%;
  padding: var(--space-md);
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--fs-body);
  font-weight: var(--fw-semibold);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s;
}

.btn-guide-start:hover {
  background: var(--accent-dim);
}

/* ── 过渡 ── */
.fade-enter-active, .fade-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out);
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>