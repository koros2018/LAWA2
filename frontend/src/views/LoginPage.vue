<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'
import { setSession } from '@/store/session'

const router = useRouter()
const username = ref('')
const lang = ref<'zh' | 'en'>('zh')
const loading = ref(false)
const error = ref('')



// 预设趣味用户名
const funnyNames = [
  '星际旅人', '月光读者', '云中漫步者',
  'StarWalker', 'DreamCatcher', 'MoonReader',
]

function pickRandomName() {
  username.value = funnyNames[Math.floor(Math.random() * funnyNames.length)]
}

async function handleLogin() {
  if (!username.value.trim()) {
    error.value = '请输入或选择一个名字'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const result = await login(username.value.trim(), lang.value)
    setSession(result)

    if (!result.has_profile) {
      // 先显示短暂的成功提示再跳转
      await new Promise(r => setTimeout(r, 600))
      router.push('/onboarding')
    } else {
      await new Promise(r => setTimeout(r, 600))
      router.push('/')
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 玄幻背景 -->
    <div class="portal-bg"></div>
    <div class="portal-ring ring-1"></div>
    <div class="portal-ring ring-2"></div>
    <div class="portal-ring ring-3"></div>
    <div class="stars"></div>

    <div class="login-container">
      <!-- Logo / 玄幻符号 -->
      <div class="sigil">
        <div class="sigil-outer">
          <div class="sigil-inner">
            <span class="sigil-icon">🌿</span>
          </div>
        </div>
      </div>

      <h1 class="app-title">LAWA</h1>
      <p class="app-subtitle">Language · World · Awakening</p>
      <p class="app-desc">语言是一扇门。<br/>跨过去，世界就在另一边。</p>
      <p class="app-desc-en">Language is a door.<br/>Step through, and the world is on the other side.</p>



      <!-- 简易登录 -->
      <div class="login-form">
        <div class="input-group">
          <label class="input-label">你的名字 · Your Name</label>
          <div class="input-row">
            <input
              v-model="username"
              type="text"
              class="input-field"
              placeholder="给自己起个名 · Pick a name"
              @keyup.enter="handleLogin"
            />
            <button class="btn-rand" @click="pickRandomName" title="随机生成 · Random">🎲</button>
          </div>
        </div>

        <div class="input-group">
          <label class="input-label">语言方向 · Language Direction</label>
          <div class="lang-toggle">
            <button
              class="lang-btn"
              :class="{ active: lang === 'zh' }"
              @click="lang = 'zh'"
            >
              🇨🇳 中文 → 英文
            </button>
            <button
              class="lang-btn"
              :class="{ active: lang === 'en' }"
              @click="lang = 'en'"
            >
              🇬🇧 English → 中文
            </button>
          </div>
        </div>

        <p v-if="error" class="error-text">{{ error }}</p>

        <button
          class="btn-enter"
          :disabled="loading"
          @click="handleLogin"
        >
          <span v-if="loading" class="loading-spinner"></span>
          <span v-else>进入 · Enter</span>
        </button>
      </div>

      <p class="footer-text">
        语言能力不是练出来的，是养出来的。<br/>
        Language isn't practiced — it's cultivated.
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: fixed;
  inset: 0;
  background: var(--bg-primary, #0a0a0f);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* ── 玄幻背景 ── */
.portal-bg {
  position: absolute;
  inset: -50%;
  background: radial-gradient(
    ellipse at 50% 40%,
    rgba(167, 139, 250, 0.12) 0%,
    transparent 60%
  );
  animation: portalPulse 4s ease-in-out infinite;
}

@keyframes portalPulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

.portal-ring {
  position: absolute;
  border: 1px solid rgba(167, 139, 250, 0.15);
  border-radius: 50%;
  animation: ringSpin 20s linear infinite;
}

.ring-1 {
  width: 70vmin;
  height: 70vmin;
  top: 15%;
  left: 15%;
}

.ring-2 {
  width: 50vmin;
  height: 50vmin;
  top: 25%;
  left: 25%;
  border-color: rgba(167, 139, 250, 0.08);
  animation-duration: 30s;
  animation-direction: reverse;
}

.ring-3 {
  width: 30vmin;
  height: 30vmin;
  top: 35%;
  left: 35%;
  border-color: rgba(167, 139, 250, 0.12);
  animation-duration: 15s;
}

@keyframes ringSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 星光粒子 */
.stars {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(1px 1px at 30% 60%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 50% 10%, rgba(255,255,255,0.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 70% 40%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(1px 1px at 85% 80%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 20% 90%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(1px 1px at 60% 70%, rgba(255,255,255,0.2) 0%, transparent 100%),
    radial-gradient(1px 1px at 40% 30%, rgba(255,255,255,0.3) 0%, transparent 100%);
  animation: twinkle 3s ease-in-out infinite alternate;
}

@keyframes twinkle {
  from { opacity: 0.6; }
  to { opacity: 1; }
}

/* ── 内容容器 ── */
.login-container {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: var(--space-xl, 2rem);
  max-width: 380px;
  width: 100%;
}

/* ── 玄幻符号 ── */
.sigil {
  margin-bottom: var(--space-xl, 2rem);
  display: flex;
  justify-content: center;
}

.sigil-outer {
  width: 72px;
  height: 72px;
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: sigilFloat 3s ease-in-out infinite;
}

@keyframes sigilFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.sigil-inner {
  width: 56px;
  height: 56px;
  background: rgba(167, 139, 250, 0.08);
  border: 1px solid rgba(167, 139, 250, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sigil-icon {
  font-size: 1.5rem;
}

/* ── 文字 ── */
.app-title {
  font-size: clamp(2rem, 6vw, 2.5rem);
  font-weight: 700;
  letter-spacing: 0.2em;
  background: linear-gradient(135deg, #f5f5f7, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: var(--space-sm, 0.5rem);
}

.app-subtitle {
  font-size: var(--fs-caption, 0.875rem);
  color: var(--text-tertiary, #6e6e73);
  letter-spacing: 0.15em;
  margin-bottom: var(--space-lg, 1.5rem);
  font-family: 'SF Mono', 'Cascadia Code', monospace;
}

.app-desc {
  font-size: var(--fs-body, 1rem);
  color: var(--text-secondary, #86868b);
  line-height: 1.6;
  margin-bottom: var(--space-xl, 2rem);
}



/* ── 表单 ── */
.login-form {
  text-align: left;
  margin-bottom: var(--space-xl, 2rem);
}

.input-group {
  margin-bottom: var(--space-lg, 1.5rem);
}

.input-label {
  display: block;
  font-size: var(--fs-caption, 0.875rem);
  color: var(--text-tertiary, #6e6e73);
  margin-bottom: var(--space-sm, 0.5rem);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input-row {
  display: flex;
  gap: var(--space-sm, 0.5rem);
}

.input-field {
  flex: 1;
  background: transparent;
  border: 1px solid var(--border, rgba(255,255,255,0.06));
  border-radius: 4px;
  padding: var(--space-md, 1rem);
  color: var(--text-primary, #f5f5f7);
  font-size: var(--fs-body, 1rem);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.input-field:focus {
  border-color: var(--accent, #a78bfa);
}

.input-field::placeholder {
  color: var(--text-tertiary, #6e6e73);
}

.btn-rand {
  width: 44px;
  height: 44px;
  background: transparent;
  border: 1px solid var(--border, rgba(255,255,255,0.06));
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s;
  flex-shrink: 0;
}

.btn-rand:hover {
  border-color: var(--accent, #a78bfa);
}

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

.lang-btn:hover:not(.active) {
  border-color: var(--border-light, rgba(255,255,255,0.1));
}

.error-text {
  color: var(--warning, #fbbf24);
  font-size: var(--fs-small, 0.75rem);
  margin-bottom: var(--space-md, 1rem);
}

.btn-enter {
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

.btn-enter:hover:not(:disabled) {
  background: var(--accent-dim, #7c5cbf);
}

.btn-enter:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.footer-text {
  font-size: var(--fs-small, 0.75rem);
  color: var(--text-tertiary, #6e6e73);
  font-style: italic;
}

/* ── 过渡 ── */
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease-out;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>