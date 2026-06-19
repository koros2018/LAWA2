<script setup lang="ts">
import { ref, onMounted } from 'vue'

const dots = ref(0)

onMounted(() => {
  const interval = setInterval(() => {
    dots.value = (dots.value + 1) % 4
  }, 500)
  onUnmounted(() => clearInterval(interval))
})
</script>

<template>
  <div class="typing-indicator">
    <span>语伴正在输入 · Partner typing</span>
    <span class="dots">
      <span v-for="i in 3" :key="i" class="dot" :class="{ active: i <= dots }"></span>
    </span>
  </div>
</template>

<style scoped>
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(167, 139, 250, 0.08);
  border-radius: 0.75rem;
  color: #a78bfa;
  font-size: 0.8rem;
}

.dots {
  display: flex;
  gap: 0.15rem;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a78bfa;
  opacity: 0.3;
  transition: opacity 0.3s;
}

.dot.active {
  opacity: 1;
}
</style>
