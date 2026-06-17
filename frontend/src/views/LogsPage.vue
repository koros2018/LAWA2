<template>
  <div class="logs-page">
    <!-- ════ 头部 ════ -->
    <header class="page-header">
      <div>
        <h1>日志查看 · Log Viewer</h1>
        <p class="subtitle">系统运行日志 · System logs</p>
      </div>
      <button v-if="session.user?.isAdmin" class="danger-btn" @click="handleClear">
        🗑️ 清空日志 · Clear
      </button>
    </header>

    <!-- ════ 统计信息 ════ -->
    <div v-if="statsLoading" class="loading-state">
      <span class="loading-spinner"></span>
      <span>加载中 · Loading...</span>
    </div>

    <div v-else-if="stats" class="stats-bar">
      <div class="stat-item">
        <span class="stat-icon">📄</span>
        <span class="stat-value">{{ stats.line_count }}</span>
        <span class="stat-label">总行数 · Total Lines</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon">💾</span>
        <span class="stat-value">{{ stats.file_size_human }}</span>
        <span class="stat-label">文件大小 · File Size</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon">🕐</span>
        <span class="stat-value">{{ formatTime(stats.last_modified || '') }}</span>
        <span class="stat-label">最后修改 · Last Modified</span>
      </div>
    </div>

    <!-- ════ 筛选栏 ════ -->
    <div class="filter-bar">
      <div class="search-input">
        <span>🔍</span>
        <input v-model="search" placeholder="搜索日志 · Search logs..." @input="loadLogs" />
      </div>
      <select v-model="level" @change="loadLogs">
        <option value="">全部级别 · All Levels</option>
        <option v-for="l in levels" :key="l" :value="l">{{ l }}</option>
      </select>
      <div class="lines-select">
        <span>行数 · Lines:</span>
        <select v-model="lines" @change="loadLogs">
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
          <option :value="500">500</option>
          <option :value="1000">1000</option>
        </select>
      </div>
      <button class="refresh-btn" @click="loadLogs">🔄 刷新 · Refresh</button>
    </div>

    <!-- ════ 日志列表 ════ -->
    <div v-if="loading" class="loading-state">
      <span class="loading-spinner"></span>
      <span>加载中 · Loading...</span>
    </div>

    <div v-else-if="logs.length === 0" class="empty-state">
      <span>📭</span>
      <p>暂无日志 · No logs</p>
    </div>

    <div v-else class="logs-list">
      <div
        v-for="(log, idx) in logs"
        :key="idx"
        class="log-entry"
        :class="log.level.toLowerCase()"
      >
        <div class="log-time">{{ formatTime(log.timestamp) }}</div>
        <div class="log-level" :style="{ color: levelColors[log.level as keyof typeof levelColors] }">
          {{ log.level }}
        </div>
        <div class="log-location">{{ log.location }}</div>
        <div class="log-message">{{ log.message }}</div>
      </div>
    </div>

    <div v-if="logs.length > 0" class="log-footer">
      显示最近 {{ logs.length }} 条 · Showing {{ logs.length }} of {{ total }} entries
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { session } from '@/store/session'
import { useLogs } from '@/api/logs'

const {
  logs,
  total,
  stats,
  loading,
  statsLoading,
  lines,
  level,
  search,
  startTime,
  endTime,
  levels,
  levelColors,
  loadLogs,
  loadStats,
  handleClear,
  formatTime,
} = useLogs()
</script>

<style scoped>
.logs-page {
  padding: 24px;
  max-width: 1200px;
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

.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-icon {
  font-size: 1.25rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #eee;
}

.stat-label {
  font-size: 0.75rem;
  color: #7f8c8d;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 8px 12px;
}

.search-input input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.9rem;
  outline: none;
  color: #eee;
}

.filter-bar select {
  padding: 8px 12px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  font-size: 0.9rem;
  background: rgba(255,255,255,0.05);
  color: #eee;
}

.lines-select {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #7f8c8d;
}

.lines-select select {
  padding: 6px 8px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 6px;
  background: rgba(255,255,255,0.05);
  color: #eee;
}

.refresh-btn {
  padding: 8px 16px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  color: #eee;
  cursor: pointer;
  font-size: 0.9rem;
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

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 600px;
  overflow-y: auto;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 12px;
}

.log-entry {
  display: grid;
  grid-template-columns: 70px 80px 200px 1fr;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  border-left: 3px solid transparent;
}

.log-entry.debug { background: rgba(96, 165, 250, 0.05); border-left-color: #60a5fa; }
.log-entry.info { background: rgba(52, 211, 153, 0.05); border-left-color: #34d399; }
.log-entry.warning { background: rgba(251, 191, 36, 0.05); border-left-color: #fbbf24; }
.log-entry.error { background: rgba(248, 113, 113, 0.05); border-left-color: #f87171; }
.log-entry.critical { background: rgba(244, 63, 94, 0.05); border-left-color: #f43f5e; }

.log-time {
  color: #7f8c8d;
  font-family: monospace;
  font-size: 0.8rem;
}

.log-level {
  font-weight: 600;
  text-transform: uppercase;
}

.log-location {
  color: #a78bfa;
  font-family: monospace;
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-message {
  color: #eee;
  word-break: break-word;
}

.log-footer {
  text-align: center;
  padding: 12px;
  font-size: 0.85rem;
  color: #7f8c8d;
  margin-top: 12px;
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
  .logs-list {
    grid-template-columns: 1fr;
  }
  .log-time, .log-level, .log-location {
    display: inline;
  }
  .log-location {
    margin-left: 8px;
  }
}
</style>
