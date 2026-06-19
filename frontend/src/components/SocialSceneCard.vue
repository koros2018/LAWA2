<script setup lang="ts">
import { ref, computed } from 'vue'
import type { SocialSceneData } from '@/api/agent_main'
import { updateSocialLevel } from '@/api/agent_main'
import { handleApiError } from '@/utils/error'

const props = defineProps<{
  scene: SocialSceneData
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

const currentLevel = ref(props.scene.understanding_level)
const busy = ref(false)

const levelLabels: Record<string, string> = {
  understand: '🟢 能看懂',
  use: '🟡 能使用',
  create: '🔴 能创作',
}

const categoryLabels: Record<string, string> = {
  net_slang: '网络用语',
  life_scene: '生活场景',
  group_chat: '群聊回复',
  meme: '梗/文化',
}

const difficultyLabel = computed(() => {
  const map: Record<string, string> = { easy: '简单', medium: '中等', hard: '较难' }
  return map[props.scene.difficulty] || props.scene.difficulty
})

const categoryLabel = computed(() => categoryLabels[props.scene.category] || props.scene.category)

async function upgradeLevel() {
  if (busy.value) return
  const next = currentLevel.value === 'understand' ? 'use' : 'create'
  busy.value = true
  try {
    await updateSocialLevel(props.scene.vocab_id, next)
    currentLevel.value = next
    emit('updated')
  } catch (e) {
    handleApiError(e, '升级失败 · Update failed', 'Failed to upgrade level')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="scene-card card">
    <div class="scene-card-header">
      <span class="scene-badge">{{ categoryLabel }}</span>
      <span class="scene-difficulty">{{ difficultyLabel }}</span>
      <span class="scene-level-tag">{{ levelLabels[currentLevel] }}</span>
    </div>

    <div class="scene-word-row">
      <span class="scene-word">{{ scene.word }}</span>
      <button
        class="btn-upgrade"
        :disabled="busy || currentLevel === 'create'"
        @click="upgradeLevel"
      >
        {{ currentLevel === 'create' ? '✅ 已掌握' : '⬆ 升级' }}
      </button>
    </div>

    <p class="scene-meaning">{{ scene.meaning }}</p>

    <div class="scene-example">
      <span class="scene-example-label">场景例句</span>
      <p class="scene-example-text">{{ scene.scene_example }}</p>
    </div>
  </div>
</template>

<style scoped>
.scene-card {
  transition: all 0.3s var(--ease-out);
  border-left: 3px solid var(--accent);
}

.scene-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.scene-badge {
  font-size: var(--fs-small);
  color: var(--accent);
  background: var(--accent-glow);
  padding: 2px 8px;
  border-radius: 4px;
}

.scene-difficulty {
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.scene-level-tag {
  font-size: var(--fs-small);
  color: var(--success);
  margin-left: auto;
}

.scene-word-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-sm);
}

.scene-word {
  font-size: clamp(1.25rem, 4vw, 1.75rem);
  font-weight: var(--fw-bold);
  color: var(--text-primary);
  letter-spacing: 0.02em;
}

.btn-upgrade {
  font-size: var(--fs-small);
  padding: 4px 12px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  min-height: 32px;
}

.btn-upgrade:hover:not(:disabled) {
  background: var(--accent-glow);
}

.btn-upgrade:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.scene-meaning {
  font-size: var(--fs-body);
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-lg);
}

.scene-example {
  background: var(--surface);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
}

.scene-example-label {
  font-size: var(--fs-small);
  color: var(--text-tertiary);
  display: block;
  margin-bottom: var(--space-xs);
}

.scene-example-text {
  font-size: var(--fs-body);
  color: var(--text-secondary);
  line-height: 1.7;
  word-break: break-word;
}

@media (max-width: 374px) {
  .scene-word {
    font-size: clamp(1rem, 4vw, 1.25rem);
  }
  .scene-example {
    padding: var(--space-sm);
  }
}
</style>