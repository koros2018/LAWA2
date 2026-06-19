import { ref, computed, onMounted } from 'vue'
import { apiGet, apiDelete } from './client'
import { handleApiError, toast } from '@/utils/error'

// ── 类型定义 ──

export interface ErrorEntry {
  type: string
  count: number
  last_seen: string
  example: string
}

// ── 底层 API 函数 ──

export async function getErrorStats(): Promise<{
  total_unique_errors: number
  total_errors: number
  top_errors: ErrorEntry[]
}> {
  return apiGet('/api/v2/errors/stats')
}

export async function clearErrorStats(): Promise<void> {
  await apiDelete('/api/v2/errors/stats')
}

// ── Composable ──

export function useErrorMonitor() {
  const stats = ref<{
    total_unique_errors: number
    total_errors: number
    top_errors: ErrorEntry[]
  } | null>(null)
  const loading = ref(false)

  const levelColors = computed(() => ({
    'ValueError': '#f87171',
    'TypeError': '#fbbf24',
    'KeyError': '#f43f5e',
    'AttributeError': '#60a5fa',
    'IndexError': '#34d399',
    'ZeroDivisionError': '#a78bfa',
    'FileNotFoundError': '#fb923c',
    'PermissionError': '#f87171',
    'ConnectionError': '#f43f5e',
    'TimeoutError': '#fb923c',
    'Exception': '#94a3b8',
  }))

  async function loadStats() {
    loading.value = true
    try {
      stats.value = await getErrorStats()
    } catch (e) {
      handleApiError(e, '加载错误统计失败 · Load failed', 'Failed to load error stats')
    } finally {
      loading.value = false
    }
  }

  async function handleClear() {
    if (confirm('确定清空错误统计？\nConfirm clear error stats?')) {
      await clearErrorStats()
      await loadStats()
    }
  }

  onMounted(() => {
    loadStats()
  })

  return {
    stats,
    loading,
    levelColors,
    loadStats,
    handleClear,
  }
}
