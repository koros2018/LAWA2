<script setup lang="ts">
import { ref, onErrorCaptured, onMounted } from 'vue'

const hasError = ref(false)
const errorMessage = ref('')

onErrorCaptured((err) => {
  hasError.value = true
  errorMessage.value = err instanceof Error ? err.message : String(err)
  console.error('[ErrorBoundary]', err)
  return false  // 阻止错误继续传播
})

function retry() {
  hasError.value = false
  errorMessage.value = ''
  window.location.reload()
}
</script>

<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-icon">⚠️</div>
    <h2 class="error-title">页面渲染失败 · Render Failed</h2>
    <p class="error-message">{{ errorMessage }}</p>
    <button class="btn btn-primary" @click="retry">🔄 刷新重试 · Retry</button>
  </div>
  <slot v-else />
</template>

<style scoped>
.error-boundary {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  padding: var(--space-3xl);
  text-align: center;
  gap: var(--space-lg);
  background: var(--bg-primary);
}

.error-icon {
  font-size: 4rem;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-12px); }
  75% { transform: translateX(12px); }
}

.error-title {
  font-size: var(--fs-title);
  color: var(--text-primary);
  margin: 0;
}

.error-message {
  font-size: var(--fs-small);
  color: var(--text-muted);
  max-width: 300px;
  word-break: break-word;
}
</style>
