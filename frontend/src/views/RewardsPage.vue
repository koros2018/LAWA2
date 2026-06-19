<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getRewards, getMilestones } from '@/api/agent_main'
import type { RewardData, MilestoneData } from '@/api/agent_main'
import { handleApiError, toast } from '@/utils/error'

const rewards = ref<RewardData[]>([])
const milestones = ref<MilestoneData[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [r, m] = await Promise.all([
      getRewards(),
      getMilestones(),
    ])
    rewards.value = r
    milestones.value = m
  } catch (e) {
    handleApiError(e, '加载奖励失败 · Load failed', 'Failed to load rewards')
  } finally {
    loading.value = false
  }
})

const defaultIcon: Record<string, string> = {
  first_action: '👣',
  streak_3: '🔥',
  streak_7: '🔥',
  vocab_10: '📖',
  vocab_50: '📚',
  vocab_100: '🎯',
  total_actions_10: '⚡',
  total_actions_50: '💪',
  total_xp_100: '⭐',
  total_xp_500: '🌟',
}
</script>

<template>
  <div class="page">
    <div class="bg-glow bg-glow-1"></div>

    <section class="hero-section rewards-hero">
      <h1 class="hero-title rewards-title">收获 · Rewards</h1>
      <p class="hero-subtitle">成长的路上，总有意想不到的惊喜。<br>Unexpected surprises along the way.</p>
    </section>

    <!-- 里程碑 -->
    <section class="milestones-section">
      <h2 class="section-title">里程碑 · Milestones</h2>
      <div class="divider"></div>

      <div v-if="loading" class="milestones-grid">
        <div v-for="i in 4" :key="i" class="card skeleton" style="height: 64px;"></div>
      </div>

      <div v-else-if="milestones.length" class="milestones-grid">
        <div
          v-for="m in milestones"
          :key="m.code"
          class="milestone-card card"
          :class="{ 'milestone-done': m.is_achieved }"
        >
          <div class="milestone-left">
            <span class="milestone-icon">{{ m.icon || defaultIcon[m.code] || '🏆' }}</span>
            <div class="milestone-info">
              <h4 class="milestone-name">{{ m.name }}</h4>
              <p class="milestone-desc">{{ m.description }}</p>
            </div>
          </div>
          <div class="milestone-right">
            <div v-if="!m.is_achieved" class="milestone-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: Math.min(100, (m.progress / m.target_value) * 100) + '%' }"></div>
              </div>
              <span class="progress-text">{{ m.progress }}/{{ m.target_value }}</span>
            </div>
            <span v-else class="milestone-check">✅</span>
          </div>
        </div>
      </div>

      <div v-else class="empty-block">
        <p>还没有里程碑。开始行动吧！<br>No milestones yet. Start taking action!</p>
      </div>
    </section>

    <!-- 最近奖励 -->
    <section class="rewards-section">
      <h2 class="section-title">最近奖励 · Recent Rewards</h2>
      <div class="divider"></div>

      <div v-if="loading">
        <div v-for="i in 3" :key="i" class="card skeleton" style="height: 60px; margin-bottom: 0.375rem;"></div>
      </div>

      <div v-else-if="rewards.length" class="rewards-list">
        <div v-for="r in rewards" :key="r.id" class="reward-item card">
          <span class="reward-icon">{{ r.reward_value?.icon || '🎁' }}</span>
          <div class="reward-content">
            <p class="reward-name">{{ r.reward_value?.name || r.reward_type }}</p>
            <p class="reward-message text-clamp-2">{{ r.reward_value?.message || '' }}</p>
          </div>
          <span class="reward-xp">+{{ r.xp_bonus }}</span>
        </div>
      </div>

      <div v-else class="empty-block">
        <p>还没有收获到奖励。多做一些微行动试试。<br>No rewards yet. Try some micro actions!</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.rewards-hero {
  padding-bottom: var(--space-xl);
}

.rewards-title {
  font-size: var(--fs-title);
}

.section-title {
  font-size: var(--fs-subtitle);
  font-weight: var(--fw-semibold);
  margin-bottom: var(--space-lg);
  color: var(--text-primary);
}

.milestones-section {
  margin-bottom: var(--space-2xl);
}

.milestones-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.milestone-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

@media (max-width: 374px) {
  .milestone-card {
    gap: var(--space-sm);
  }
}

.milestone-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex: 1;
  min-width: 0;
}

@media (max-width: 374px) {
  .milestone-left {
    gap: var(--space-sm);
  }
}

.milestone-icon {
  font-size: clamp(1.25rem, 4vw, 1.5rem);
  flex-shrink: 0;
}

.milestone-info {
  min-width: 0;
}

.milestone-name {
  font-size: var(--fs-body);
  font-weight: var(--fw-medium);
  color: var(--text-primary);
}

.milestone-desc {
  font-size: var(--fs-small);
  color: var(--text-secondary);
  margin-top: 2px;
}

.milestone-right {
  flex-shrink: 0;
  min-width: 72px;
  text-align: right;
}

@media (max-width: 374px) {
  .milestone-right {
    min-width: 60px;
  }
}

.milestone-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.progress-bar {
  width: 72px;
  height: 4px;
  background: var(--bg-primary);
  border-radius: 2px;
  overflow: hidden;
}

@media (max-width: 374px) {
  .progress-bar {
    width: 60px;
  }
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width var(--duration-slow) var(--ease-out);
}

.progress-text {
  font-size: var(--fs-small);
  color: var(--text-tertiary);
}

.milestone-check {
  font-size: 1.25rem;
}

.milestone-done {
  border-color: rgba(52, 211, 153, 0.2);
}

/* ── 奖励列表 ── */
.rewards-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.reward-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
}

@media (max-width: 374px) {
  .reward-item {
    gap: var(--space-sm);
  }
}

.reward-icon {
  font-size: clamp(1.25rem, 4vw, 1.5rem);
  flex-shrink: 0;
  margin-top: 2px;
}

.reward-content {
  flex: 1;
  min-width: 0;
}

.reward-name {
  font-size: var(--fs-body);
  font-weight: var(--fw-medium);
  color: var(--text-primary);
}

.reward-message {
  font-size: var(--fs-small);
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.4;
}

.reward-xp {
  font-size: var(--fs-caption);
  font-weight: var(--fw-semibold);
  color: var(--success);
  flex-shrink: 0;
}

.empty-block {
  text-align: center;
  padding: var(--space-xl) 0;
  color: var(--text-tertiary);
}
</style>