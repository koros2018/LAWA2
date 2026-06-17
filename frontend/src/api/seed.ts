import { ref, computed } from 'vue'
import { getSeedContents, createSeedContent, updateSeedContent, deleteSeedContent, getSystemContents, SeedContent } from './seed'

const CONTENT_TYPES = [
  { value: 'social_scene', label: '社交场景 · Social Scene', label_en: 'Social Scene' },
  { value: 'push_message', label: '推送文案 · Push Message', label_en: 'Push Message' },
  { value: 'culture_tip', label: '文化背景 · Culture Tip', label_en: 'Culture Tip' },
  { value: 'holiday_info', label: '节假日信息 · Holiday Info', label_en: 'Holiday Info' },
  { value: 'vocabulary_card', label: '词汇卡片 · Vocabulary Card', label_en: 'Vocabulary Card' },
]

const DIFFICULTIES = [
  { value: 'beginner', label: '初级 · Beginner', label_en: 'Beginner' },
  { value: 'intermediate', label: '中级 · Intermediate', label_en: 'Intermediate' },
  { value: 'advanced', label: '高级 · Advanced', label_en: 'Advanced' },
]

export function useSeedContent() {
  const contents = ref<SeedContent[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const search = ref('')
  const selectedType = ref<string | null>(null)
  const editingContent = ref<SeedContent | null>(null)
  const showModal = ref(false)

  const filteredContents = computed(() => {
    let result = contents.value
    if (selectedType.value) {
      result = result.filter(c => c.content_type === selectedType.value)
    }
    if (search.value) {
      const q = search.value.toLowerCase()
      result = result.filter(c =>
        c.title.toLowerCase().includes(q) ||
        c.title_en.toLowerCase().includes(q) ||
        (c.content && c.content.toLowerCase().includes(q))
      )
    }
    return result
  })

  const typeLabels = computed(() => {
    const map: Record<string, { label: string, label_en: string }> = {}
    CONTENT_TYPES.forEach(t => {
      map[t.value] = { label: t.label, label_en: t.label_en }
    })
    return map
  })

  const difficultyLabels = computed(() => {
    const map: Record<string, { label: string, label_en: string }> = {}
    DIFFICULTIES.forEach(d => {
      map[d.value] = { label: d.label, label_en: d.label_en }
    })
    return map
  })

  async function loadContents() {
    loading.value = true
    try {
      const result = await getSeedContents({
        page: page.value,
        page_size: pageSize.value,
        search: search.value || undefined,
        content_type: selectedType.value || undefined,
      })
      contents.value = result.items
      total.value = result.total
    } catch (e) {
      console.error('Failed to load seed contents:', e)
    } finally {
      loading.value = false
    }
  }

  async function saveContent(data: Partial<SeedContent>) {
    if (editingContent.value?.id) {
      const updated = await updateSeedContent(editingContent.value.id, data)
      await loadContents()
      return updated
    } else {
      const created = await createSeedContent({
        content_type: data.content_type || 'social_scene',
        title: data.title || '',
        title_en: data.title_en || '',
        content: data.content || null,
        content_en: data.content_en || null,
        tags: data.tags || [],
        difficulty: data.difficulty || null,
      })
      await loadContents()
      return created
    }
  }

  async function removeContent(id: number) {
    await deleteSeedContent(id)
    await loadContents()
  }

  function openEdit(content?: SeedContent) {
    editingContent.value = content ? { ...content } : {
      content_type: 'social_scene',
      title: '',
      title_en: '',
      content: '',
      content_en: '',
      tags: [],
      difficulty: 'beginner',
      is_active: true,
      is_system: false,
    }
    showModal.value = true
  }

  function closeEdit() {
    editingContent.value = null
    showModal.value = false
  }

  return {
    contents: filteredContents,
    total,
    page,
    pageSize,
    loading,
    search,
    selectedType,
    editingContent,
    showModal,
    CONTENT_TYPES,
    DIFFICULTIES,
    typeLabels,
    difficultyLabels,
    loadContents,
    saveContent,
    removeContent,
    openEdit,
    closeEdit,
  }
}
