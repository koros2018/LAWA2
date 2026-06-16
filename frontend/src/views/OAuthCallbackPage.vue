<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { setSession } from '@/store/session'

const router = useRouter()
const route = useRoute()
const errorMsg = ref('')

onMounted(() => {
  const token = route.query.token as string
  const userId = route.query.user_id as string
  const isNew = route.query.is_new === 'true'
  const provider = route.query.provider as string

  if (token && userId) {
    // 先获取用户信息
    fetch(`/api/v2/auth/me?user_id=${userId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(json => {
        if (json.status === 'ok') {
          const u = json.data
          setSession({
            user_id: userId,
            username: u.username,
            display_name: u.display_name || '',
            native_lang: u.native_lang,
            learn_lang: u.learn_lang,
            interests: u.interests || [],
            current_level: u.current_level || null,
            has_profile: u.current_level !== null,
            is_new_user: isNew,
            token,
          })
          router.push(isNew ? '/onboarding' : '/')
        } else {
          // fallback：直接用 token
          localStorage.setItem('lawa2_session', JSON.stringify({
            userId, token,
            hasProfile: !isNew,
            isNewUser: isNew,
          }))
          router.push(isNew ? '/onboarding' : '/')
        }
      })
      .catch(() => {
        // fallback
        localStorage.setItem('lawa2_session', JSON.stringify({
          userId, token,
          hasProfile: !isNew,
          isNewUser: isNew,
        }))
        router.push(isNew ? '/onboarding' : '/')
      })
  } else {
    errorMsg.value = '登录失败，请重试 · Login failed, please try again'
    setTimeout(() => router.push('/login'), 3000)
  }
})
</script>

<template>
  <div class="oauth-callback-page">
    <div v-if="!errorMsg" class="loading-section">
      <div class="loading-spinner"></div>
      <p class="loading-text">正在登录 · Logging in with {{ route.query.provider || 'OAuth' }}...</p>
    </div>
    <div v-else class="error-section">
      <span class="error-icon">⚠️</span>
      <p class="error-text">{{ errorMsg }}</p>
      <p class="redirect-hint">3 秒后跳转登录页 · Redirecting...</p>
    </div>
  </div>
</template>

<style scoped>
.oauth-callback-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #0a0a1a 0%, #0f0f2a 100%);
  padding: 1rem;
}
.loading-section, .error-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid rgba(167, 139, 250, 0.2);
  border-top-color: #a78bfa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { color: #aaa; font-size: 0.9rem; }
.error-icon { font-size: 2rem; }
.error-text { color: #f44336; font-size: 0.9rem; text-align: center; }
.redirect-hint { color: #666; font-size: 0.75rem; }
</style>