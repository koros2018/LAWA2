<script setup lang="ts">
import { computed } from 'vue'
import { toast } from '@/utils/error'

const toastType = computed(() => toast.value?.type ?? 'info')
const toastClass = computed(() => `toast toast-${toastType.value}`)
</script>

<template>
  <div v-if="toast" class="toast-container">
    <div :class="toastClass">
      <span class="toast-icon">{{ toastType === 'error' ? '⚠️' : toastType === 'success' ? '✅' : toastType === 'warning' ? '⚡' : 'ℹ️' }}</span>
      <div class="toast-content">
        <p class="toast-message">{{ toast.message }}</p>
        <p class="toast-message-en" v-if="toast.messageEn && toast.message !== toast.messageEn">{{ toast.messageEn }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  animation: toastIn 0.3s ease-out;
}

@keyframes toastIn {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
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

.toast-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.toast-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toast-message {
  font-weight: var(--fw-medium);
}

.toast-message-en {
  font-size: var(--fs-small);
  opacity: 0.7;
}
</style>
