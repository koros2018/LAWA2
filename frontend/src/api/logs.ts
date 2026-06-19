import { ref, computed, onMounted } from 'vue'
import { apiGet, apiDelete } from './client'
import { handleApiError, toast } from '@/utils/error'

// ── 类型定义 ──

export interface LogEntry {
  line: string
  level: string
  timestamp: string
  message: string
}

// ── 底层 API 函数 ──

export async function getLogs(params: {
  lines?: number
  level?: string
  search?: string
  start_time?: string
  end_time?: string
}): Promise<{ logs: LogEntry[]; total: number }> {
  const query = new URLSearchParams()
  if (params.lines) query.set('lines', String(params.lines))
  if (params.level) query.set('level', params.level)
  if (params.search) query.set('search', params.search)
  if (params.start_time) query.set('start_time', params.start_time)
  if (params.end_time) query.set('end_time', params.end_time)
  const qs = query.toString()
  return apiGet<{ logs: LogEntry[]; total: number }>(`/api/v2/logs${qs ? `?${qs}` : ''}`)
}

export async function getLogStats(): Promise<{
  file_size: number
  file_size_human: string
  line_count: number
  last_modified: string | null
}> {
  return apiGet('/api/v2/logs/stats')
}

export async function clearLogs(): Promise<void> {
  await apiDelete('/api/v2/logs')
}

// ── Composable ──

export function useLogs() {
  const logs = ref<LogEntry[]>([])
  const total = ref(0)
  const stats = ref<{
    file_size: number
    file_size_human: string
    line_count: number
    last_modified: string | null
  } | null>(null)
  const loading = ref(false)
  const statsLoading = ref(false)

  const lines = ref(100)
  const level = ref<string | null>(null)
  const search = ref('')
  const startTime = ref<string | null>(null)
  const endTime = ref<string | null>(null)

  const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

  const levelColors = computed(() => ({
    DEBUG: '#60a5fa',
    INFO: '#34d399',
    WARNING: '#fbbf24',
    ERROR: '#f87171',
    CRITICAL: '#f43f5e',
  }))

  async function loadLogs() {
    loading.value = true
    try {
      const result = await getLogs({
        lines: lines.value,
        level: level.value || undefined,
        search: search.value || undefined,
        start_time: startTime.value || undefined,
        end_time: endTime.value || undefined,
      })
      logs.value = result.logs
      total.value = result.total
    } catch (e) {
      handleApiError(e, '加载日志失败 · Load failed', 'Failed to load logs')
    } finally {
      loading.value = false
    }
  }

  async function loadStats() {
    statsLoading.value = true
    try {
      stats.value = await getLogStats()
    } catch (e) {
      handleApiError(e, '加载统计失败 · Load failed', 'Failed to load stats')
    } finally {
      statsLoading.value = false
    }
  }

  async function handleClear() {
    if (confirm('确定清空所有日志？\nConfirm clear all logs?')) {
      await clearLogs()
      await loadLogs()
      await loadStats()
    }
  }

  function formatTime(iso: string): string {
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

  onMounted(() => {
    loadLogs()
    loadStats()
  })

  return {
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
  }
}
