<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { handleApiError, toast } from '@/utils/error'
import {
  listWordCards,
  getReviewQueue,
  reviewWordCard,
  getWordCardStats,
  createWordCard,
  deleteWordCard,
  syncFromCompanion,
} from '@/api/word_card'
import type { WordCard, ReviewQueueItem, WordCardStats } from '@/api/word_card'

const tab = ref<'browse' | 'review' | 'stats'>('stats')
const cards = ref<WordCard[]>([])
const reviewQueue = ref<ReviewQueueItem[]>([])
const stats = ref<WordCardStats | null>(null)
const loading = ref(false)
const search = ref('')
const masteredFilter = ref<boolean | null>(null)
const currentReview = ref<ReviewQueueItem | null>(null)
const showDefinition = ref(false)
const showExample = ref(false)
const reviewMessage = ref('')
const syncing = ref(false)
const showAddModal = ref(false)
const newCard = ref({ word: '', definition: '', definition_native: '', part_of_speech: '', example_sentence: '' })

async function loadCards() {
  loading.value = true
  try {
    const result = await listWordCards({ lang: 'en', search: search.value || undefined, mastered: masteredFilter.value })
    cards.value = result.items
  } catch (e) { handleApiError(e, '加载卡片失败 · Load failed', 'Failed to load cards') }
  finally { loading.value = false }
}

async function loadReviewQueue() {
  loading.value = true
  try {
    const result = await getReviewQueue('en', 50)
    reviewQueue.value = result.queue
  } catch (e) { handleApiError(e, '加载复习队列失败 · Load failed', 'Failed to load review queue') }
  finally { loading.value = false }
}

async function loadStats() {
  try { stats.value = await getWordCardStats('en') }
  catch (e) { handleApiError(e, '加载统计失败 · Load failed', 'Failed to load stats') }
}

async function startReview() {
  await loadReviewQueue()
  if (reviewQueue.value.length > 0) {
    currentReview.value = reviewQueue.value[0]
    showDefinition.value = false
    showExample.value = false
  }
  tab.value = 'review'
}

async function submitReview(quality: number) {
  if (!currentReview.value) return
  try {
    await reviewWordCard(currentReview.value.id, quality)
    reviewQueue.value = reviewQueue.value.filter(r => r.id !== currentReview.value!.id)
    if (reviewQueue.value.length > 0) {
      currentReview.value = reviewQueue.value[0]
      showDefinition.value = false
      showExample.value = false
    } else {
      currentReview.value = null
      reviewMessage.value = '🎉 全部复习完毕！'
      setTimeout(() => { reviewMessage.value = ''; tab.value = 'browse'; loadCards() }, 2000)
    }
  } catch (e) { handleApiError(e, '提交复习失败 · Submit failed', 'Failed to submit review') }
}

async function handleAddCard() {
  try {
    await createWordCard({
      word: newCard.value.word,
      definition: newCard.value.definition || undefined,
      definition_native: newCard.value.definition_native || undefined,
      part_of_speech: newCard.value.part_of_speech || undefined,
      example_sentence: newCard.value.example_sentence || undefined,
    })
    newCard.value = { word: '', definition: '', definition_native: '', part_of_speech: '', example_sentence: '' }
    showAddModal.value = false
    await loadCards()
    await loadStats()
  } catch (e) { handleApiError(e, '添加卡片失败 · Add failed', 'Failed to add card') }
}

async function handleDelete(cardId: string) {
  if (!confirm('确定删除这张卡片？')) return
  try {
    await deleteWordCard(cardId)
    await loadCards()
    await loadStats()
  } catch (e) { handleApiError(e, '删除卡片失败 · Delete failed', 'Failed to delete card') }
}

async function handleSync() {
  syncing.value = true
  try {
    const result = await syncFromCompanion()
    reviewMessage.value = `同步完成：${result.synced} 张卡片`
    await loadCards()
    await loadStats()
    setTimeout(() => { reviewMessage.value = '' }, 3000)
  } catch (e) { handleApiError(e, '同步失败 · Sync failed', 'Failed to sync') }
  finally { syncing.value = false }
}

function nextReview() {
  reviewQueue.value = reviewQueue.value.slice(1)
  if (reviewQueue.value.length > 0) {
    currentReview.value = reviewQueue.value[0]
    showDefinition.value = false
    showExample.value = false
  } else { currentReview.value = null }
}

const formatDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => loadStats())
</script>

<template>
  <div class="wc-page">
    <div class="wc-header">
      <h2>📚 词汇卡片</h2>
      <div class="wc-tabs">
        <button :class="{ active: tab === 'stats' }" @click="tab='stats'; loadStats()">📊</button>
        <button :class="{ active: tab === 'browse' }" @click="tab='browse'; loadCards()">📖</button>
        <button :class="{ active: tab === 'review' }" @click="startReview()">🔄</button>
      </div>
    </div>

    <!-- Stats -->
    <div v-if="tab === 'stats' && stats" class="wc-section">
      <div class="wc-grid-4">
        <div class="wc-stat"><span class="wc-num">{{ stats.total }}</span>总卡片</div>
        <div class="wc-stat"><span class="wc-num">{{ stats.learning }}</span>学习中</div>
        <div class="wc-stat"><span class="wc-num">{{ stats.mastered }}</span>已掌握</div>
        <div class="wc-stat due"><span class="wc-num">{{ stats.due_today }}</span>待复习</div>
      </div>
      <div class="wc-bar">
        <div class="wc-bar-label">掌握率 {{ stats.mastery_rate }}%</div>
        <div class="wc-bar-track"><div class="wc-bar-fill" :style="{ width: stats.mastery_rate + '%' }"></div></div>
      </div>
      <div class="wc-actions">
        <button class="btn-pri" @click="startReview()">🔄 开始复习 ({{ stats.due_today }})</button>
        <button class="btn-sec" @click="showAddModal = true">✏️ 添加</button>
        <button class="btn-sec" :disabled="syncing" @click="handleSync">{{ syncing ? '同步中...' : '📥 同步伴读' }}</button>
      </div>
    </div>

    <!-- Browse -->
    <div v-if="tab === 'browse'" class="wc-section">
      <div class="wc-tools">
        <input v-model="search" placeholder="搜索..." class="wc-input" @input="loadCards" />
        <select v-model="masteredFilter" class="wc-select" @change="loadCards">
          <option :value="null">全部</option>
          <option :value="false">学习中</option>
          <option :value="true">已掌握</option>
        </select>
      </div>
      <div v-if="loading" class="wc-loading">加载中...</div>
      <div v-else-if="cards.length === 0" class="wc-empty">
        <p>📚 暂无卡片 · No cards yet</p>
        <button class="btn-pri" @click="showAddModal = true">✏️ 添加第一张 · Add First Card</button>
      </div>
      <div v-else class="wc-list">
        <div v-for="card in cards" :key="card.id" class="wc-item">
          <div class="wc-item-top">
            <strong>{{ card.word }}</strong>
            <span v-if="card.part_of_speech" class="wc-pos">{{ card.part_of_speech }}</span>
            <span v-if="card.is_mastered" class="wc-badge">✅</span>
          </div>
          <div class="wc-item-def">{{ card.definition || card.definition_native || '-' }}</div>
          <div class="wc-item-meta">
            <span>复习 {{ card.review_count }} 次</span>
            <span v-if="card.next_review_at">下次 {{ formatDate(card.next_review_at) }}</span>
          </div>
          <button class="wc-del" @click="handleDelete(card.id)">🗑️</button>
        </div>
      </div>
    </div>

    <!-- Review -->
    <div v-if="tab === 'review'" class="wc-section">
      <div v-if="reviewMessage" class="wc-msg">{{ reviewMessage }}</div>
      <div v-else-if="!currentReview" class="wc-empty">
        <p>🎉 没有待复习词汇</p>
        <button class="btn-pri" @click="tab='browse'; loadCards()">浏览卡片</button>
      </div>
      <div v-else class="wc-review">
        <div class="wc-progress">剩余 {{ reviewQueue.length }} 张</div>
        <div class="wc-flashcard">
          <div class="wc-fc-word">{{ currentReview.word }}</div>
          <div v-if="currentReview.part_of_speech" class="wc-fc-pos">{{ currentReview.part_of_speech }}</div>
          <div v-if="!showDefinition" class="wc-fc-hint">还记得意思吗？</div>
          <div v-if="showDefinition" class="wc-fc-def">{{ currentReview.definition || currentReview.definition_native }}</div>
          <div v-if="showExample && currentReview.example_sentence" class="wc-fc-ex"><em>{{ currentReview.example_sentence }}</em></div>
          <div class="wc-fc-stats">复习 {{ currentReview.review_count }} 次</div>
        </div>
        <div class="wc-reveal-btns">
          <button class="btn-rev" @click="showDefinition = !showDefinition">{{ showDefinition ? '🙈' : '👀' }} 释义</button>
          <button class="btn-rev" @click="showExample = !showExample">{{ showExample ? '🙈' : '📝' }} 例句</button>
        </div>
        <div class="wc-quality">
          <button class="q q0" @click="submitReview(0)">😵 忘了</button>
          <button class="q q1" @click="submitReview(1)">😅 模糊</button>
          <button class="q q2" @click="submitReview(2)">🤔 勉强</button>
          <button class="q q3" @click="submitReview(3)">😊 正确</button>
          <button class="q q4" @click="submitReview(4)">👍 轻松</button>
          <button class="q q5" @click="submitReview(5)">🔥 完美</button>
        </div>
        <button class="btn-skip" @click="nextReview">⏭️ 跳过</button>
      </div>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="wc-overlay" @click.self="showAddModal = false">
      <div class="wc-modal">
        <h3>✏️ 添加卡片</h3>
        <div class="wc-fg"><label>单词 *</label><input v-model="newCard.word" placeholder="ubiquitous" /></div>
        <div class="wc-fg"><label>英文释义</label><input v-model="newCard.definition" placeholder="existing everywhere" /></div>
        <div class="wc-fg"><label>中文释义</label><input v-model="newCard.definition_native" placeholder="无处不在的" /></div>
        <div class="wc-fg"><label>词性</label><input v-model="newCard.part_of_speech" placeholder="adjective" /></div>
        <div class="wc-fg"><label>例句</label><textarea v-model="newCard.example_sentence" placeholder="Smartphones have become ubiquitous."></textarea></div>
        <div class="wc-modal-acts">
          <button class="btn-sec" @click="showAddModal = false">取消</button>
          <button class="btn-pri" :disabled="!newCard.word" @click="handleAddCard">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wc-page { padding: 1rem; padding-top: 4rem; padding-bottom: 6rem; max-width: 600px; margin: 0 auto; }
.wc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.wc-header h2 { font-size: 1.1rem; margin: 0; color: var(--text, #e0e0e0); }
.wc-tabs { display: flex; gap: 0.3rem; }
.wc-tabs button { padding: 0.3rem 0.5rem; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.4rem; background: rgba(255,255,255,0.05); color: var(--text-muted, #888); cursor: pointer; font-size: 1rem; transition: all 0.2s; }
.wc-tabs button.active { background: rgba(167,139,250,0.2); border-color: var(--accent, #a78bfa); color: var(--accent, #a78bfa); }

.wc-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-bottom: 1rem; }
.wc-stat { background: rgba(255,255,255,0.05); border-radius: 0.6rem; padding: 0.6rem 0.3rem; text-align: center; border: 1px solid rgba(255,255,255,0.06); font-size: 0.65rem; color: var(--text-muted, #888); }
.wc-num { display: block; font-size: 1.3rem; font-weight: 700; color: var(--accent, #a78bfa); margin-bottom: 0.1rem; }
.wc-stat.due .wc-num { color: #fbbf24; }

.wc-bar { margin-bottom: 1rem; }
.wc-bar-label { font-size: 0.75rem; color: var(--text-muted, #888); margin-bottom: 0.3rem; }
.wc-bar-track { height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; }
.wc-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent, #a78bfa), #c084fc); border-radius: 3px; transition: width 0.5s ease; }

.wc-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.btn-pri { flex: 1; padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; background: linear-gradient(135deg, var(--accent, #a78bfa), #c084fc); color: #fff; cursor: pointer; font-size: 0.85rem; }
.btn-sec { padding: 0.5rem 0.8rem; border: 1px solid rgba(255,255,255,0.15); border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: var(--text, #ccc); cursor: pointer; font-size: 0.8rem; }
.btn-sec:disabled { opacity: 0.5; cursor: not-allowed; }

.wc-tools { display: flex; gap: 0.5rem; margin-bottom: 0.8rem; }
.wc-input { flex: 1; padding: 0.4rem 0.6rem; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.4rem; background: rgba(255,255,255,0.05); color: var(--text, #ccc); font-size: 0.85rem; }
.wc-select { padding: 0.4rem 0.6rem; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.4rem; background: rgba(15,15,30,0.9); color: var(--text, #ccc); font-size: 0.85rem; }

.wc-loading, .wc-empty { text-align: center; padding: 2rem 0; color: var(--text-muted, #888); }
.wc-empty .btn-pri { margin-top: 1rem; }

.wc-list { display: flex; flex-direction: column; gap: 0.5rem; }
.wc-item { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 0.6rem; padding: 0.7rem; position: relative; }
.wc-item-top { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem; }
.wc-item-top strong { font-size: 0.95rem; color: var(--text, #e0e0e0); }
.wc-pos { font-size: 0.7rem; color: var(--text-muted, #666); font-style: italic; }
.wc-badge { font-size: 0.75rem; }
.wc-item-def { font-size: 0.8rem; color: var(--text-muted, #888); margin-bottom: 0.3rem; }
.wc-item-meta { display: flex; gap: 0.8rem; font-size: 0.65rem; color: var(--text-muted, #666); }
.wc-del { position: absolute; top: 0.4rem; right: 0.4rem; background: none; border: none; cursor: pointer; font-size: 0.8rem; opacity: 0.5; }
.wc-del:hover { opacity: 1; }

/* Review */
.wc-review { animation: fadeIn 0.3s ease; }
.wc-progress { text-align: center; font-size: 0.8rem; color: var(--text-muted, #888); margin-bottom: 0.8rem; }
.wc-flashcard { background: rgba(167,139,250,0.08); border: 1px solid rgba(167,139,250,0.2); border-radius: 1rem; padding: 2rem 1.5rem; text-align: center; margin-bottom: 1rem; min-height: 180px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.wc-fc-word { font-size: 1.6rem; font-weight: 700; color: var(--accent, #a78bfa); margin-bottom: 0.3rem; }
.wc-fc-pos { font-size: 0.75rem; color: var(--text-muted, #666); margin-bottom: 0.8rem; }
.wc-fc-hint { font-size: 0.85rem; color: var(--text-muted, #888); }
.wc-fc-def { font-size: 1rem; color: var(--text, #e0e0e0); margin-bottom: 0.5rem; }
.wc-fc-ex { font-size: 0.85rem; color: var(--text-muted, #999); margin-bottom: 0.5rem; }
.wc-fc-stats { font-size: 0.7rem; color: var(--text-muted, #666); }

.wc-reveal-btns { display: flex; gap: 0.5rem; justify-content: center; margin-bottom: 1rem; }
.btn-rev { padding: 0.35rem 0.8rem; border: 1px solid rgba(255,255,255,0.12); border-radius: 0.4rem; background: rgba(255,255,255,0.05); color: var(--text, #ccc); cursor: pointer; font-size: 0.8rem; }

.wc-quality { display: flex; flex-wrap: wrap; gap: 0.3rem; justify-content: center; margin-bottom: 1rem; }
.q { padding: 0.4rem 0.6rem; border: 1px solid rgba(255,255,255,0.08); border-radius: 0.5rem; background: rgba(255,255,255,0.04); color: var(--text, #ccc); cursor: pointer; font-size: 0.75rem; transition: all 0.15s; }
.q:hover { transform: scale(1.05); }
.q.q0 { border-color: #ef4444; background: rgba(239,68,68,0.05); }
.q.q1 { border-color: #f97316; background: rgba(249,115,22,0.05); }
.q.q2 { border-color: #eab308; background: rgba(234,179,8,0.05); }
.q.q3 { border-color: #22c55e; background: rgba(34,197,94,0.05); }
.q.q4 { border-color: #06b6d4; background: rgba(6,182,212,0.05); }
.q.q5 { border-color: #a78bfa; background: rgba(167,139,250,0.08); }
.q:active { transform: scale(0.95); }
.q.q5:hover { box-shadow: 0 0 12px rgba(167,139,250,0.4); }
.q0 { border-color: #ef4444; }
.q1 { border-color: #f97316; }
.q2 { border-color: #eab308; }
.q3 { border-color: #22c55e; }
.q4 { border-color: #06b6d4; }
.q5 { border-color: #a78bfa; }

.btn-skip { display: block; margin: 0 auto; padding: 0.4rem 1rem; border: 1px solid rgba(255,255,255,0.08); border-radius: 0.4rem; background: transparent; color: var(--text-muted, #666); cursor: pointer; font-size: 0.75rem; }

.wc-msg { text-align: center; padding: 2rem; font-size: 1rem; color: var(--accent, #a78bfa); }

/* Modal */
.wc-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.wc-modal { background: #1a1a2e; border: 1px solid rgba(255,255,255,0.08); border-radius: 0.8rem; padding: 1.2rem; width: 90%; max-width: 400px; max-height: 85vh; overflow-y: auto; }
.wc-modal h3 { margin: 0 0 0.8rem; font-size: 1rem; color: var(--text, #e0e0e0); }
.wc-fg { margin-bottom: 0.6rem; }
.wc-fg label { display: block; font-size: 0.75rem; color: var(--text-muted, #888); margin-bottom: 0.2rem; }
.wc-fg input, .wc-fg textarea { width: 100%; padding: 0.4rem 0.5rem; border: 1px solid rgba(255,255,255,0.1); border-radius: 0.4rem; background: rgba(255,255,255,0.05); color: var(--text, #ccc); font-size: 0.85rem; box-sizing: border-box; }
.wc-fg textarea { resize: vertical; min-height: 50px; }
.wc-modal-acts { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 0.8rem; }
.wc-modal-acts .btn-pri { flex: 0 auto; }
.wc-modal-acts .btn-sec { flex: 0 auto; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
