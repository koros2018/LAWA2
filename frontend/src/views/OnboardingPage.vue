<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { saveProfile } from '@/api/auth'
import { session, updateProfile } from '@/store/session'

const router = useRouter()

const displayName = ref(session.user?.displayName || session.user?.username || '')
const learnLang = ref<'en' | 'zh'>(
  session.user?.nativeLang === 'zh' ? 'en' : 'zh'
)
const level = ref('')
const selectedInterests = ref<string[]>([])
const loading = ref(false)
const error = ref('')
const step = ref(1) // 1=名字, 2=兴趣+水平

const allInterests = {
  en: [
    { id: 'tech', label: '科技 · Tech' },
    { id: 'news', label: '新闻 · News' },
    { id: 'culture', label: '文化 · Culture' },
    { id: 'life', label: '生活 · Life' },
    { id: 'sports', label: '体育 · Sports' },
    { id: 'entertainment', label: '娱乐 · Entertainment' },
    { id: 'business', label: '商业 · Business' },
    { id: 'science', label: '科学 · Science' },
  ],
  zh: [
    { id: 'daily', label: 'Daily Life' },
    { id: 'news', label: 'News' },
    { id: 'culture', label: 'Culture' },
    { id: 'food', label: 'Food' },
    { id: 'travel', label: 'Travel' },
    { id: 'tech', label: 'Tech' },
    { id: 'entertainment', label: 'Entertainment' },
    { id: 'literature', label: 'Literature' },
  ],
}

const levels = [
  { id: 'beginner', label: '零基础 · Beginner', enLabel: 'Beginner' },
  { id: 'elementary', label: '初级 · Elementary', enLabel: 'Elementary' },
  { id: 'intermediate', label: '中级 · Intermediate', enLabel: 'Intermediate' },
  { id: 'upper', label: '中高级 · Upper Intermediate', enLabel: 'Upper Intermediate' },
  { id: 'advanced', label: '高级 · Advanced', enLabel: 'Advanced' },
]

const currentInterests = computed(() =>
  session.user?.nativeLang === 'zh' ? allInterests.zh : allInterests.en
)

function toggleInterest(id: string) {
  const i = selectedInterests.value.indexOf(id)
  if (i >= 0) {
    selectedInterests.value.splice(i, 1)
  } else {
    selectedInterests.value.push(id)
  }
}

function nextStep() {
  if (!displayName.value.trim()) {
    error.value = '给自己起个名字吧 · Please pick a name'
    return
  }
  error.value = ''
  step.value = 2
}

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    const result = await saveProfile({
      username: session.user!.username,
      display_name: displayName.value.trim(),
      native_lang: session.user!.nativeLang,
      learn_lang: learnLang.value,
      interests: selectedInterests.value,
      current_level: level.value || null,
    })
    updateProfile(result)
    router.push('/')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败 · Save failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="onboarding-page">
    <div class="bg-glow bg-glow-1"></div>

    <div class="onboarding-container">
      <!-- 进度指示 -->
      <div class="progress-dots">
        <span class="dot" :class="{ active: step >= 1 }"></span>
        <span class="dot-line"></span>
        <span class="dot" :class="{ active: step >= 2 }"></span>
      </div>

      <Transition name="fade-slide" mode="out-in">
        <!-- Step 1: 名字 -->
        <div v-if="step === 1" key="step1" class="step-content">
          <div class="step-icon">🌿</div>
          <h1 class="step-title">你叫什么名字？<br><span class="step-title-en">What's your name?</span></h1>
          <p class="step-desc">
            语言花园需要一位园丁。<br/>
            给它一个名字，它就有了主人。<br/>
            Your garden needs a gardener.
          </p>
          <p class="step-desc-en">
            Every garden needs a gardener.<br/>
            Give it a name, and it's yours.
          </p>

          <div class="input-group">
            <input
              v-model="displayName"
              type="text"
              class="input-field"
              placeholder="你的名字 · Your name"
              maxlength="30"
              @keyup.enter="nextStep"
            />
          </div>

          <p v-if="error" class="error-text">{{ error }}</p>

          <button class="btn-next" @click="nextStep">
            下一步 · Next →
          </button>

          <button class="btn-skip" @click="step = 2">
            跳过 · Skip →
          </button>
        </div>

        <!-- Step 2: 兴趣 + 水平 -->
        <div v-else key="step2" class="step-content">
          <div class="step-icon">🎯</div>
          <h1 class="step-title">你想学什么？<br><span class="step-title-en">What do you want to learn?</span></h1>
          <p class="step-desc">
            选择你感兴趣的内容，<br/>
            你的花园就会朝着那个方向生长。<br/>
            Your garden grows toward your interests.
          </p>
          <p class="step-desc-en">
            Pick what interests you.<br/>
            Your garden grows in the direction you water.
          </p>

          <!-- 目标语言 -->
          <div class="input-group">
            <label class="input-label">学习目标语言 · Target Language</label>
            <div class="lang-toggle">
              <button
                v-if="session.user?.nativeLang === 'zh'"
                class="lang-btn"
                :class="{ active: learnLang === 'en' }"
                @click="learnLang = 'en'"
              >🇬🇧 English</button>
              <button
                v-if="session.user?.nativeLang === 'en'"
                class="lang-btn"
                :class="{ active: learnLang === 'zh' }"
                @click="learnLang = 'zh'"
              >🇨🇳 中文</button>
            </div>
          </div>

          <!-- 兴趣标签 -->
          <div class="input-group">
            <label class="input-label">兴趣领域 · Interests <span class="input-hint">（可多选 · Multiple）</span></label>
            <div class="tag-grid">
              <button
                v-for="t in currentInterests"
                :key="t.id"
                class="tag-btn"
                :class="{ selected: selectedInterests.includes(t.id) }"
                @click="toggleInterest(t.id)"
              >
                {{ t.label }}
              </button>
            </div>
          </div>

          <!-- 水平 -->
          <div class="input-group">
            <label class="input-label">当前水平 · Current Level <span class="input-hint">（选填 · Optional）</span></label>
            <div class="level-grid">
              <button
                v-for="l in levels"
                :key="l.id"
                class="level-btn"
                :class="{ selected: level === l.id }"
                @click="level = level === l.id ? '' : l.id"
              >
                {{ session.user?.nativeLang === 'zh' ? l.label : l.enLabel }}
              </button>
            </div>
          </div>

          <p v-if="error" class="error-text">{{ error }}</p>

          <button
            class="btn-enter"
            :disabled="loading"
            @click="handleSubmit"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>开始养成 · Start Growing</span>
          </button>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.onboarding-page {
  position: fixed;
  inset: 0;
  background: var(--bg-primary, #0a0a0f);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
}

.onboarding-container {
  position: relative;
  z-index: 1;
  padding: var(--space-xl, 2rem);
  max-width: 420px;
  width: 100%;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* ── 进度点 ── */
.progress-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: var(--space-2xl, 3rem);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--text-tertiary, #6e6e73);
  transition: all 0.3s;
}

.dot.active {
  background: var(--accent, #a78bfa);
  box-shadow: 0 0 8px var(--accent, #a78bfa);
}

.dot-line {
  width: 40px;
  height: 1px;
  background: var(--border, rgba(255,255,255,0.06));
}

/* ── Step 内容 ── */
.step-content {
  text-align: center;
}

.step-icon {
  font-size: 2.5rem;
  margin-bottom: var(--space-lg, 1.5rem);
}

.step-title {
  font-size: var(--fs-title, clamp(1.25rem, 4vw, 2rem));
  font-weight: 700;
  color: var(--text-primary, #f5f5f7);
  margin-bottom: var(--space-md, 1rem);
}

.step-desc {
  font-size: var(--fs-body, 1rem);
  color: var(--text-secondary, #86868b);
  line-height: 1.6;
  margin-bottom: var(--space-xl, 2rem);
}

/* ── 表单 ── */
.input-group {
  margin-bottom: var(--space-lg, 1.5rem);
  text-align: left;
}

.input-label {
  display: block;
  font-size: var(--fs-caption, 0.875rem);
  color: var(--text-tertiary, #6e6e73);
  margin-bottom: var(--space-sm, 0.5rem);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input-field {
  width: 100%;
  background: transparent;
  border: 1px solid var(--border, rgba(255,255,255,0.06));
  border-radius: 4px;
  padding: var(--space-md, 1rem);
  color: var(--text-primary, #f5f5f7);
  font-size: var(--fs-body, 1rem);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
  text-align: center;
}

.input-field:focus {
  border-color: var(--accent, #a78bfa);
}

.input-field::placeholder {
  color: var(--text-tertiary, #6e6e73);
  text-align: center;
}

.error-text {
  color: var(--warning, #fbbf24);
  font-size: var(--fs-small, 0.75rem);
  margin-bottom: var(--space-md, 1rem);
}

/* ── 按钮 ── */
.btn-next, .btn-enter {
  width: 100%;
  padding: var(--space-md, 1rem);
  background: var(--accent, #a78bfa);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: var(--fs-body, 1rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-next:hover, .btn-enter:hover:not(:disabled) {
  background: var(--accent-dim, #7c5cbf);
}

.btn-enter:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-skip {
  width: 100%;
  margin-top: var(--space-sm, 0.5rem);
  background: transparent;
  border: none;
  padding: var(--space-md, 1rem);
  color: var(--text-tertiary, #6e6e73);
  font-size: var(--fs-caption, 0.875rem);
  cursor: pointer;
  font-family: inherit;
  transition: color 0.2s;
}

.btn-skip:hover {
  color: var(--text-secondary, #86868b);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── 兴趣标签 ── */
.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm, 0.5rem);
}

.tag-btn {
  padding: var(--space-sm, 0.5rem) var(--space-lg, 1.5rem);
  background: transparent;
  border: 1px solid var(--border, rgba(255,255,255,0.06));
  border-radius: 4px;
  color: var(--text-secondary, #86868b);
  font-size: var(--fs-caption, 0.875rem);
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.tag-btn.selected {
  border-color: var(--accent, #a78bfa);
  color: var(--accent, #a78bfa);
  background: rgba(167, 139, 250, 0.08);
}

.tag-btn:hover:not(.selected) {
  border-color: var(--border-light, rgba(255,255,255,0.1));
  color: var(--text-primary, #f5f5f7);
}

/* ── 水平选择 ── */
.level-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm, 0.5rem);
}

.level-btn {
  padding: var(--space-sm, 0.5rem) var(--space-md, 1rem);
  background: transparent;
  border: 1px solid var(--border, rgba(255,255,255,0.06));
  border-radius: 4px;
  color: var(--text-secondary, #86868b);
  font-size: var(--fs-small, 0.75rem);
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.level-btn.selected {
  border-color: var(--accent, #a78bfa);
  color: var(--accent, #a78bfa);
  background: rgba(167, 139, 250, 0.08);
}

.level-btn:hover:not(.selected) {
  border-color: var(--border-light, rgba(255,255,255,0.1));
  color: var(--text-primary, #f5f5f7);
}

/* ── 语言切换 ── */
.lang-toggle {
  display: flex;
  gap: var(--space-sm, 0.5rem);
}

.lang-btn {
  flex: 1;
  background: transparent;
  border: 1px solid var(--border, rgba(255,255,255,0.06));
  border-radius: 4px;
  padding: var(--space-md, 1rem);
  color: var(--text-secondary, #86868b);
  font-size: var(--fs-caption, 0.875rem);
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  text-align: center;
}

.lang-btn.active {
  border-color: var(--accent, #a78bfa);
  color: var(--accent, #a78bfa);
  background: rgba(167, 139, 250, 0.08);
}

/* ── 过渡 ── */
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.3s ease-out;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>