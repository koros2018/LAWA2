import { ref, computed, onMounted } from 'vue'
import { getErrorStats, clearErrorStats, ErrorEntry } from './errors'

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
      console.error('Failed to load error stats:', e)
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
