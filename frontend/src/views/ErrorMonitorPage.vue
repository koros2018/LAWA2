<template>
  <div class="errors-page">
    <!-- ════ 头部 ════ -->
    <header class="page-header">
      <div>
        <h1>错误监控 · Error Monitor</h1>
        <p class="subtitle">系统错误统计 · System error statistics</p>
      </div>
      <button v-if="session.user?.isAdmin" class="danger-btn" @click="handleClear">
        🗑️ 清空统计 · Clear
      </button>
    </header>

    <!-- ════ 统计概览 ════ -->
    <div v-if="loading" class="loading-state">
      <span class="loading-spinner"></span>
      <span>加载中 · Loading...</span>
    </div>

    <div v-else-if="stats" class="stats-overview">
      <div class="stat-card">
        <div class="stat-icon">🔴</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_errors }}</div>
          <div class="stat-label">总错误数 · Total Errors</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_unique_errors }}</div>
          <div class="stat-label">不同错误类型 · Unique Types</div>
        </div>
      </div>
    </div>

    <!-- ════ Top 错误列表 ════ -->
    <div v-else-if="stats?.top_errors?.length" class="errors-section">
      <h3 class="section-title">🔥 Top 10 错误 · Top Errors</h3>
      <div class="errors-list">
        <div v-for="(error, idx) in stats.top_errors" :key="error.error_type" class="error-item">
          <div class="error-rank">{{ idx + 1 }}</div>
          <div class="error-type" :style="{ color: levelColors[error.error_type as keyof typeof levelColors] || '#94a3b8' }">
            {{ error.error_type }}
          </div>
          <div class="error-count">
            {{ error.count }} 次 · {{ error.count }}x
          </div>
          <div class="error-time">
            {{ formatTime(error.last_occurred) }}
          </div>
          <div class="error-sample" v-if="error.sample_message">
            {{ error.sample_message }}
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <span>✅</span>
      <p>暂无错误 · No errors recorded</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { session } from '@/store/session'
import { useErrorMonitor } from '@/api/errors'

const {
  stats,
  loading,
  levelColors,
  loadStats,
  handleClear,
} = useErrorMonitor()

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso
  }
}
</script>

<style scoped>
.errors-page {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 1.5rem;
  margin: 0;
  color: #eee;
}

.subtitle {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin: 4px 0 0 0;
}

.stats-overview {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 2rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #eee;
}

.stat-label {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.errors-section {
  margin-top: 24px;
}

.section-title {
  font-size: 1rem;
  color: #eee;
  margin-bottom: 16px;
}

.errors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-item {
  display: grid;
  grid-template-columns: 32px 160px 80px 120px 1fr;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: 8px;
}

.error-rank {
  font-size: 0.9rem;
  font-weight: 600;
  color: #a78bfa;
}

.error-type {
  font-weight: 600;
  font-size: 0.95rem;
}

.error-count {
  font-size: 0.9rem;
  color: #fbbf24;
  font-weight: 500;
}

.error-time {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.error-sample {
  font-size: 0.85rem;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: #7f8c8d;
}

.loading-state span,
.empty-state span {
  font-size: 2rem;
  display: block;
  margin-bottom: 8px;
}

.loading-spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid rgba(167, 139, 250, 0.2);
  border-top-color: #a78bfa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.danger-btn {
  padding: 10px 20px;
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
  border: 1px solid rgba(248, 113, 113, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}

.danger-btn:hover {
  background: rgba(248, 113, 113, 0.25);
}

@media (max-width: 768px) {
  .error-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
