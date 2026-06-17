<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getFeed, recordAction, getSocialScene, updateSocialLevel } from '@/api/agent_main'
import type { FeedData, ActionResponse, SocialSceneData } from '@/api/agent_main'

const activeTab = ref<'feed' | 'social'>('feed')

// ── Feed tab ──
const feed = ref<FeedData | null>(null)
const feedLoading = ref(true)
const actionResult = ref<ActionResponse | null>(null)
const actionBusy = ref(false)

// ── Social tab ──
const scene = ref<SocialSceneData | null>(null)
const sceneLoading = ref(false)
const sceneLevel = ref<string>('understand')

const langDir = computed(() => {
  try {
    const raw = localStorage.getItem('lawa2_session')
    if (!raw) return 'zh'
    const s = JSON.parse(raw)
    return s?.learnLang === 'zh' ? 'en' : 'zh'
  } catch {
    return 'zh'
  }
})

onMounted(async () => {
  try {
    feed.value = await getFeed()
  } catch (e) {
    console.error(e)
  } finally {
    feedLoading.value = false
  }
})

async function handleAction(code: string) {
  if (actionBusy.value || !feed.value) return
  actionBusy.value = true
  try {
    actionResult.value = await recordAction({
      habit_code: code,
      duration_seconds: 20,
      completion_status: 'completed',
      triggered_by: 'manual',
      feed_id: feed.value.feed_id,
    })
  } catch (e) {
    console.error(e)
  }
  setTimeout(() => {
    actionResult.value = null
    actionBusy.value = false
  }, 2500)
}

function refreshFeed() {
  feedLoading.value = true
  getFeed().then(f => { feed.value = f }).catch(console.error).finally(() => { feedLoading.value = false })
}

// ── Social scene ──
async function loadScene() {
  sceneLoading.value = true
  scene.value = null
  try {
    scene.value = await getSocialScene(langDir.value)
  } catch (e) {
    console.error(e)
  } finally {
    sceneLoading.value = false
  }
}

async function levelUp(vocabId: string) {
  const next = scene.value?.understanding_level === 'understand' ? 'use' : 'create'
  try {
    await updateSocialLevel(vocabId, next)
    if (scene.value) scene.value.understanding_level = next
  } catch (e) {
    console.error(e)
  }
}

function switchTab(tab: 'feed' | 'social') {
  activeTab.value = tab
  if (tab === 'social' && !scene.value && !sceneLoading.value) {
    loadScene()
  }
}

const categoryLabel = (cat: string) => {
  const labels: Record<string, string> = {
    net_slang: '🌐 网络用语 · Net Slang',
    life_scene: '🍜 生活场景 · Daily Life',
    group_chat: '💬 群聊回复 · Group Chat',
    meme: '😂 文化梗 · Meme',
  }
  return labels[cat] || cat
}

const levelLabel = (lvl: string) => {
  const labels: Record<string, string> = {
    understand: '🟢 能看懂 · Understand',
    use: '🟡 能使用 · Use',
    create: '🔴 能创作 · Create',
  }
  return labels[lvl] || lvl
}
</script>

<template>
  <div class="page">
    <div class="bg-glow bg-glow-1"></div>

    <section class="hero-section feed-hero">
      <div class="bg-glow bg-glow-4"></div>
      <h1 class="hero-title feed-title">信息流 · Feed</h1>
      <p class="hero-subtitle">你的日常语言养料<br/>读一条，都是浇灌。<br/>Your daily language nourishment · Every read is watering your garden</p>
      <!-- removed, merged into hero-subtitle above -->
    </section>

    <!-- Tab toggle -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'feed' }"
        @click="switchTab('feed')"
      >
        📰 资讯 · Feed
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'social' }"
        @click="switchTab('social')"
      >
        🗣️ 社交场景 · Social Scene
      </button>
    </div>

    <!-- ═══════════════ Feed tab ═══════════════ -->
    <template v-if="activeTab === 'feed'">
      <div v-if="feedLoading" class="feed-card card">
        <div class="skeleton" style="height: 1rem; width: 5rem; margin-bottom: 0.75rem;"></div>
        <div class="skeleton" style="height: 1rem; width: 100%; margin-bottom: 0.5rem;"></div>
        <div class="skeleton" style="height: 1rem; width: 70%;"></div>
      </div>

      <div v-else-if="feed" class="feed-card card">
        <div class="feed-card-meta">
          <span class="badge">{{ feed.content_type }}</span>
          <span class="feed-difficulty">{{ feed.difficulty }}</span>
          <span class="feed-source">{{ feed.source }}</span>
        </div>
        <p class="feed-card-text">{{ feed.text }}</p>

        <div v-if="feed.vocab_hints?.length" class="feed-vocab">
          <span class="vocab-label">生词 · Vocabulary</span>
          <span class="vocab-chip" v-for="w in feed.vocab_hints" :key="w">{{ w }}</span>
        </div>

        <div class="feed-card-actions" v-if="!actionResult">
          <button
            class="btn btn-outline btn-sm"
            @click="handleAction('read_one_post')"
            :disabled="actionBusy"
          >
            📰 读完 · Read
          </button>
          <button
            class="btn btn-outline btn-sm"
            @click="handleAction('say_one_thing')"
            :disabled="actionBusy"
          >
            🎤 跟读 · Repeat
          </button>
          <button
            class="btn btn-outline btn-sm"
            @click="handleAction('look_up_one')"
            :disabled="actionBusy"
          >
            🔍 查词 · Look Up
          </button>
        </div>

        <Transition name="slide">
          <div v-if="actionResult" class="feed-feedback">
            <span class="fb-icon">✨</span>
            <span class="fb-xp">+{{ actionResult.xp_earned }} XP</span>
            <span class="fb-streak">🔥 {{ actionResult.streak_days }} 天 · {{ actionResult.streak_days }} days</span>
            <span v-if="actionResult.reward" class="fb-reward">
              🎁 {{ actionResult.reward.reward_value?.icon }} {{ actionResult.reward.reward_value?.name }}
            </span>
          </div>
        </Transition>
      </div>

      <div v-else class="empty-state">
        <p class="empty-icon">📡</p>
        <p>暂无信息流 · No feed content available</p>
        <button class="btn btn-primary" @click="refreshFeed">刷新 · Refresh</button>
      </div>
    </template>

    <!-- ═══════════════ Social scene tab ═══════════════ -->
    <template v-if="activeTab === 'social'">
      <div v-if="sceneLoading" class="feed-card card">
        <div class="skeleton" style="height: 1rem; width: 6rem; margin-bottom: 0.75rem;"></div>
        <div class="skeleton" style="height: 1rem; width: 100%; margin-bottom: 0.5rem;"></div>
        <div class="skeleton" style="height: 1rem; width: 80%;"></div>
      </div>

      <div v-else-if="scene" class="scene-card card">
        <div class="scene-header">
          <span class="badge badge-accent">{{ categoryLabel(scene.category) }}</span>
          <span class="scene-difficulty">{{ scene.difficulty }}</span>
        </div>

        <div class="scene-word">{{ scene.word }}</div>
        <p class="scene-meaning">{{ scene.meaning }}</p>

        <div class="scene-example-box">
          <span class="scene-example-label">💡 场景例句 · Example</span>
          <p class="scene-example-text">{{ scene.scene_example }}</p>
        </div>

        <div class="scene-level-bar">
          <span class="scene-level-label">你的理解等级 · Your Understanding</span>
          <div class="level-dots">
            <span class="level-dot" :class="{ filled: scene.understanding_level === 'understand' || scene.understanding_level === 'use' || scene.understanding_level === 'create' }">🟢</span>
            <span class="level-dot" :class="{ filled: scene.understanding_level === 'use' || scene.understanding_level === 'create' }">🟡</span>
            <span class="level-dot" :class="{ filled: scene.understanding_level === 'create' }">🔴</span>
          </div>
          <div class="level-labels">
            <span>能看懂 · Understand</span>
            <span>能使用 · Use</span>
            <span>能创作 · Create</span>
          </div>
        </div>

        <div class="scene-actions">
          <button
            class="btn btn-outline btn-sm"
            @click="levelUp(scene.vocab_id)"
            :disabled="scene?.understanding_level === 'create'"
          >
            🎯 我学会了 · Got it!
          </button>
          <button class="btn btn-outline btn-sm" @click="loadScene">
            🔄 换一个 · Next
          </button>
        </div>
      </div>

      <div v-else class="empty-state">
        <p class="empty-icon">🗣️</p>
        <p>加载社交场景<br>Loading social scene</p>
        <button class="btn btn-primary" @click="loadScene">开始预演 · Start Rehearsal</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.feed-hero {
  padding-bottom: var(--space-xl);
}

.feed-title {
  font-size: var(--fs-title);
}

/* ── Tab bar ── */
.tab-bar {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-lg);
  background: var(--surface);
  border-radius: var(--radius-sm);
  padding: 3px;
  overflow: hidden;
}

.tab-btn {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: var(--fs-caption);
  font-weight: var(--fw-medium);
  border-radius: calc(var(--radius-sm) - 2px);
  cursor: pointer;
  transition: all var(--duration-normal);
  min-height: 38px;
}

.tab-btn.active {
  background: var(--accent-glow);
  color: var(--accent);
  border: 1px solid var(--accent);
}

@media (max-width: 374px) {
  .tab-btn {
    font-size: var(--fs-small);
    padding: var(--space-xs) var(--space-sm);
    min-height: 34px;
  }
}

/* ── Social scene card ── */
.scene-card {
  transition: all var(--duration-normal) var(--ease-out);
}

.scene-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.badge-accent {
  background: rgba(167, 139, 250, 0.15);
  color: var(--accent);
}

.scene-difficulty {
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
}

.scene-word {
  font-size: clamp(1.5rem, 6vw, 2.25rem);
  font-weight: var(--fw-bold);
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
  word-break: break-word;
}

.scene-meaning {
  font-size: var(--fs-body);
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
}

.scene-example-box {
  background: var(--surface);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
}

.scene-example-label {
  display: block;
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.scene-example-text {
  font-size: var(--fs-caption);
  line-height: 1.6;
  color: var(--text-secondary);
  font-style: italic;
  word-break: break-word;
}

.scene-level-bar {
  margin-bottom: var(--space-lg);
}

.scene-level-label {
  display: block;
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.level-dots {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: 2px;
}

.level-dot {
  font-size: 1.2rem;
  opacity: 0.3;
  transition: opacity var(--duration-normal);
}

.level-dot.filled {
  opacity: 1;
}

.level-labels {
  display: flex;
  gap: var(--space-xs);
  font-size: var(--fs-small);
  color: var(--text-tertiary);
}

.level-labels span {
  flex: 1;
}

.scene-actions {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

/* ── Shared styles ── */
.feed-card {
  transition: all var(--duration-normal) var(--ease-out);
}

.feed-card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.feed-difficulty {
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
}

.feed-source {
  font-size: var(--fs-small);
  color: var(--text-tertiary);
}

.feed-card-text {
  font-size: var(--fs-body);
  line-height: 1.7;
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
  word-break: break-word;
}

.feed-vocab {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex-wrap: wrap;
  margin-bottom: var(--space-lg);
}

.vocab-label {
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  margin-right: var(--space-xs);
}

.vocab-chip {
  font-size: var(--fs-small);
  color: var(--accent);
  background: var(--accent-glow);
  padding: 2px 8px;
  border-radius: 4px;
}

.feed-card-actions {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.btn-sm {
  padding: var(--space-xs) var(--space-md);
  font-size: var(--fs-caption);
  min-height: 36px;
}

@media (max-width: 374px) {
  .btn-sm {
    font-size: var(--fs-small);
    padding: var(--space-xs) var(--space-sm);
    min-height: 32px;
  }
}

.feed-feedback {
  padding: var(--space-md);
  background: var(--accent-glow);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  font-size: var(--fs-caption);
  font-weight: var(--fw-medium);
}

@media (max-width: 374px) {
  .feed-feedback {
    font-size: var(--fs-small);
    gap: var(--space-xs);
    padding: var(--space-sm);
  }
}

.fb-icon {
  font-size: 1.1rem;
}

.fb-xp {
  color: var(--success);
}

.fb-streak {
  color: var(--warning);
}

.fb-reward {
  color: var(--accent);
}

.empty-state {
  text-align: center;
  padding: var(--space-3xl) 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: 3rem;
}

.slide-enter-active, .slide-leave-active {
  transition: all var(--duration-normal) var(--ease-out);
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>