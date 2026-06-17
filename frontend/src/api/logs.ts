import { ref, computed, onMounted } from 'vue'
import { getLogs, getLogStats, clearLogs, LogEntry } from './logs'

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
      console.error('Failed to load logs:', e)
    } finally {
      loading.value = false
    }
  }

  async function loadStats() {
    statsLoading.value = true
    try {
      stats.value = await getLogStats()
    } catch (e) {
      console.error('Failed to load stats:', e)
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
