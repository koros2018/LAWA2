<template>
  <div class="conversation-page">
    <div class="page-header">
      <h1>💬 对话 · Conversation</h1>
      <p class="header-sub">AI 对话 · 智能纠错 · 多轮记忆</p>
    </div>

    <div v-if="!currentConv" class="conv-list-section">
      <div class="conv-toolbar">
        <button class="btn-primary" @click="showNewDialog = true">➕ 新对话 · New Conversation</button>
      </div>
      <div v-if="loading" class="loading-state">
        <span class="loading-spinner"></span><span>加载中... Loading...</span>
      </div>
      <div v-else-if="conversations.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <p class="empty-title">还没有对话 · No Conversations Yet</p>
        <p class="empty-desc">开始一段 AI 对话，练习你的语言能力<br/>Start a conversation to practice your language skills</p>
        <button class="btn-primary" @click="showNewDialog = true">开始对话 · Start</button>
      </div>
      <div v-else class="conv-list">
        <div v-for="conv in conversations" :key="conv.id" class="conv-card" @click="openConversation(conv.id)">
          <div class="conv-card-header">
            <span class="conv-topic">{{ conv.topic || '无主题 · Untitled' }}</span>
            <span class="conv-level">Lv.{{ conv.level }}</span>
          </div>
          <div class="conv-card-meta">
            <span>📝 {{ conv.word_count }} 词 · words</span>
            <span>🕐 {{ formatDate(conv.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="chat-section">
      <div class="chat-header">
        <button class="btn-back" @click="closeConversation">← 返回 · Back</button>
        <span class="chat-title">{{ currentConv.topic || '对话 · Conversation' }}</span>
        <div class="chat-actions">
          <label class="toggle-label">
            <input type="checkbox" v-model="enableCorrection" />
            <span class="toggle-text">纠错 · Correct</span>
          </label>
          <label class="toggle-label">
            <input type="checkbox" v-model="showEnglish" />
            <span class="toggle-text">EN</span>
          </label>
          <button class="btn-icon" @click="showCorrections = !showCorrections" title="纠错记录 · Corrections">📝</button>
          <button class="btn-icon danger" @click="confirmDelete" title="删除 · Delete">🗑️</button>
        </div>
      </div>

      <div v-if="showCorrections" class="corrections-panel">
        <div class="corrections-header">
          <h3>📝 纠错记录 · Corrections</h3>
          <button class="btn-close" @click="showCorrections = false">✕</button>
        </div>
        <div v-if="corrections.length === 0" class="corrections-empty">暂无纠错记录 · No corrections yet</div>
        <div v-for="c in corrections" :key="c.id" class="correction-item">
          <div class="corr-original">❌ {{ c.original }}</div>
          <div class="corr-corrected">✅ {{ c.corrected }}</div>
          <div v-if="c.explanation" class="corr-explain">{{ c.explanation }}</div>
        </div>
      </div>

      <div ref="messageListRef" class="message-list">
        <div v-if="messages.length === 0" class="empty-chat">
          <p>发送第一条消息开始对话<br/>Send your first message to start</p>
        </div>
        <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
          <div class="msg-bubble">
            <div class="msg-content">{{ msg.content }}</div>
            <div v-if="showEnglish && msg.content_en" class="msg-english">{{ msg.content_en }}</div>
            <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>
        <div v-if="aiLoading" class="message assistant">
          <div class="msg-bubble typing"><TypingIndicator /></div>
        </div>
      </div>

      <div class="input-area">
        <textarea v-model="userInput" class="chat-input" :placeholder="'输入消息... Type a message...'" rows="2" @keydown.enter.prevent="sendMessage" :disabled="aiLoading"></textarea>
        <div class="input-actions">
          <label class="level-label">Level:
            <select v-model.number="level">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="4">4</option>
              <option :value="5">5</option>
            </select>
          </label>
          <button class="btn-send" :disabled="!userInput.trim() || aiLoading" @click="sendMessage">{{ aiLoading ? '...' : '发送 · Send' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showNewDialog" class="dialog-overlay" @click.self="showNewDialog = false">
      <div class="dialog-card">
        <h2>新建对话 · New Conversation</h2>
        <input v-model="newTopic" class="dialog-input" placeholder="对话主题 · Topic (可选)" @keydown.enter="createConversation" />
        <div class="dialog-actions">
          <button class="btn-ghost" @click="showNewDialog = false">取消 · Cancel</button>
          <button class="btn-primary" @click="createConversation" :disabled="creating">{{ creating ? '创建中...' : '创建 · Create' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import TypingIndicator from '../components/TypingIndicator.vue'
import { handleApiError } from '../utils/error'
import { createConversation as apiCreateConv, getConversation, getUserConversations, generateAIResponse, deleteConversation, getCorrections } from '../api/conversation'
import type { Conversation, ConversationMessage, Correction } from '../api/conversation'

const loading = ref(true)
const conversations = ref<Conversation[]>([])
const currentConv = ref<Conversation | null>(null)
const messages = ref<ConversationMessage[]>([])
const corrections = ref<Correction[]>([])
const userInput = ref('')
const level = ref(1)
const enableCorrection = ref(true)
const showEnglish = ref(true)
const showCorrections = ref(false)
const aiLoading = ref(false)
const creating = ref(false)
const showNewDialog = ref(false)
const newTopic = ref('')
const messageListRef = ref<HTMLElement | null>(null)

onMounted(() => { loadConversations() })

async function loadConversations() {
  loading.value = true
  try { conversations.value = await getUserConversations() }
  catch (e: any) { handleApiError(e, '加载对话列表失败 · Failed to load conversations') }
  finally { loading.value = false }
}

async function openConversation(id: number) {
  try {
    const conv = await getConversation(id)
    currentConv.value = conv
    messages.value = conv.messages || []
    try { const res = await getCorrections(id); corrections.value = res.corrections }
    catch { corrections.value = [] }
    await nextTick(); scrollToBottom()
  } catch (e: any) { handleApiError(e, '加载对话失败 · Failed to load conversation') }
}

function closeConversation() {
  currentConv.value = null; messages.value = []; corrections.value = []; showCorrections.value = false
  loadConversations()
}

async function createConversation() {
  if (creating.value) return
  creating.value = true
  try {
    const conv = await apiCreateConv(newTopic.value || undefined)
    showNewDialog.value = false; newTopic.value = ''
    await openConversation(conv.id)
  } catch (e: any) { handleApiError(e, '创建对话失败 · Failed to create conversation') }
  finally { creating.value = false }
}

async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || !currentConv.value || aiLoading.value) return
  userInput.value = ''
  const tempMsg: ConversationMessage = { id: -Date.now(), role: 'user', content: text, content_en: null, order: messages.value.length + 1, created_at: new Date().toISOString() }
  messages.value.push(tempMsg)
  scrollToBottom()
  aiLoading.value = true
  try {
    const response = await generateAIResponse(currentConv.value.id, text, level.value, enableCorrection.value)
    const aiMsg: ConversationMessage = { id: -Date.now() - 1, role: 'assistant', content: response.content, content_en: response.content_en, order: messages.value.length + 1, created_at: new Date().toISOString() }
    messages.value.push(aiMsg)
    if (response.correction?.original) {
      try { const res = await getCorrections(currentConv.value.id); corrections.value = res.corrections } catch { /* ignore */ }
    }
    await nextTick(); scrollToBottom()
  } catch (e: any) {
    handleApiError(e, 'AI 回复失败 · AI response failed', 'AI 暂时无法回复，请稍后重试')
    messages.value = messages.value.filter(m => m.id !== tempMsg.id)
  } finally { aiLoading.value = false }
}

async function confirmDelete() {
  if (!currentConv.value) return
  if (!confirm('确定删除这个对话？· Delete this conversation?')) return
  try { await deleteConversation(currentConv.value.id); closeConversation() }
  catch (e: any) { handleApiError(e, '删除失败 · Delete failed') }
}

function scrollToBottom() { if (messageListRef.value) messageListRef.value.scrollTop = messageListRef.value.scrollHeight }
function formatDate(iso: string | null): string { if (!iso) return '—'; return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }
function formatTime(iso: string | null): string { if (!iso) return ''; return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
</script>

<style scoped>
.conversation-page { min-height: 100dvh; background: linear-gradient(180deg, #0a0a1a 0%, #0f0f2a 100%); padding: 1rem; padding-bottom: calc(1rem + env(safe-area-inset-bottom, 0px) + 5rem); color: #e0e0f0; }
.page-header { text-align: center; padding: 1rem 0 0.5rem; }
.page-header h1 { font-size: 1.4rem; margin: 0; background: linear-gradient(135deg, #a78bfa, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.header-sub { font-size: 0.8rem; color: #8888aa; margin: 0.3rem 0 0; }
.conv-toolbar { display: flex; justify-content: center; padding: 0.8rem 0; }
.btn-primary { padding: 0.6rem 1.4rem; border: none; border-radius: 12px; background: linear-gradient(135deg, #7c3aed, #a78bfa); color: #fff; font-size: 0.9rem; cursor: pointer; transition: all 0.2s; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary:not(:disabled):hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4); }
.btn-back { padding: 0.4rem 0.8rem; border: 1px solid #333366; border-radius: 8px; background: transparent; color: #a78bfa; font-size: 0.85rem; cursor: pointer; }
.btn-icon { padding: 0.4rem 0.6rem; border: none; border-radius: 8px; background: rgba(255,255,255,0.05); cursor: pointer; font-size: 1rem; transition: all 0.2s; }
.btn-icon:hover { background: rgba(255,255,255,0.1); }
.btn-icon.danger:hover { background: rgba(255,50,50,0.2); }
.btn-ghost { padding: 0.5rem 1rem; border: 1px solid #333366; border-radius: 8px; background: transparent; color: #a78bfa; cursor: pointer; }
.btn-send { padding: 0.5rem 1.2rem; border: none; border-radius: 10px; background: linear-gradient(135deg, #7c3aed, #a78bfa); color: #fff; font-size: 0.9rem; cursor: pointer; transition: all 0.2s; }
.btn-send:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-send:not(:disabled):hover { transform: translateY(-1px); }
.btn-close { border: none; background: transparent; color: #8888aa; font-size: 1.1rem; cursor: pointer; }
.loading-state { display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 3rem 1rem; color: #8888aa; }
.loading-spinner { width: 20px; height: 20px; border: 2px solid #333366; border-top-color: #a78bfa; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { text-align: center; padding: 3rem 1rem; }
.empty-icon { font-size: 3rem; margin-bottom: 0.5rem; }
.empty-title { font-size: 1.1rem; color: #a78bfa; margin: 0.5rem 0; }
.empty-desc { font-size: 0.85rem; color: #8888aa; margin: 0.3rem 0 1rem; line-height: 1.5; }
.conv-list { display: flex; flex-direction: column; gap: 0.6rem; }
.conv-card { padding: 0.8rem 1rem; border-radius: 12px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); cursor: pointer; transition: all 0.2s; }
.conv-card:hover { background: rgba(255,255,255,0.08); border-color: rgba(167, 139, 250, 0.3); }
.conv-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem; }
.conv-topic { font-size: 1rem; font-weight: 500; color: #e0e0f0; }
.conv-level { font-size: 0.8rem; color: #a78bfa; background: rgba(167,139,250,0.15); padding: 0.15rem 0.5rem; border-radius: 6px; }
.conv-card-meta { display: flex; gap: 1rem; font-size: 0.8rem; color: #8888aa; }
.chat-section { display: flex; flex-direction: column; height: calc(100dvh - 6rem); }
.chat-header { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.06); flex-shrink: 0; }
.chat-title { flex: 1; font-size: 1rem; font-weight: 500; color: #e0e0f0; }
.chat-actions { display: flex; align-items: center; gap: 0.4rem; }
.toggle-label { display: flex; align-items: center; gap: 0.3rem; cursor: pointer; font-size: 0.8rem; color: #8888aa; }
.toggle-label input[type="checkbox"] { accent-color: #a78bfa; }
.corrections-panel { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 0.8rem; margin: 0.5rem 0; max-height: 40vh; overflow-y: auto; flex-shrink: 0; }
.corrections-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.corrections-header h3 { font-size: 0.9rem; color: #a78bfa; margin: 0; }
.corrections-empty { text-align: center; padding: 1rem; color: #8888aa; font-size: 0.85rem; }
.correction-item { padding: 0.5rem; margin-bottom: 0.4rem; background: rgba(255,255,255,0.03); border-radius: 8px; }
.corr-original { color: #f87171; font-size: 0.85rem; }
.corr-corrected { color: #34d399; font-size: 0.85rem; }
.corr-explain { color: #8888aa; font-size: 0.8rem; margin-top: 0.2rem; font-style: italic; }
.message-list { flex: 1; overflow-y: auto; padding: 0.8rem 0; display: flex; flex-direction: column; gap: 0.6rem; }
.empty-chat { text-align: center; padding: 2rem 1rem; color: #8888aa; font-size: 0.85rem; }
.message { display: flex; }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }
.msg-bubble { max-width: 80%; padding: 0.6rem 0.8rem; border-radius: 12px; line-height: 1.5; }
.message.user .msg-bubble { background: rgba(124, 58, 237, 0.3); border: 1px solid rgba(167, 139, 250, 0.3); }
.message.assistant .msg-bubble { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); }
.msg-english { font-size: 0.8rem; color: #a78bfa; margin-top: 0.3rem; }
.msg-time { font-size: 0.7rem; color: #666688; margin-top: 0.3rem; text-align: right; }
.msg-bubble.typing { padding: 0.8rem 1rem; }
.input-area { flex-shrink: 0; border-top: 1px solid rgba(255,255,255,0.06); padding: 0.5rem 0; }
.chat-input { width: 100%; padding: 0.6rem; border: 1px solid #333366; border-radius: 10px; background: rgba(255,255,255,0.03); color: #e0e0f0; font-size: 0.9rem; resize: none; outline: none; box-sizing: border-box; }
.chat-input:focus { border-color: #7c3aed; }
.chat-input::placeholder { color: #555577; }
.input-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem; }
.level-label { font-size: 0.8rem; color: #8888aa; display: flex; align-items: center; gap: 0.3rem; }
.level-label select { background: rgba(255,255,255,0.05); color: #e0e0f0; border: 1px solid #333366; border-radius: 6px; padding: 0.2rem 0.4rem; font-size: 0.8rem; }
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: #1a1a3a; border: 1px solid #333366; border-radius: 16px; padding: 1.5rem; width: 90%; max-width: 400px; }
.dialog-card h2 { font-size: 1.1rem; color: #a78bfa; margin: 0 0 1rem; }
.dialog-input { width: 100%; padding: 0.6rem; border: 1px solid #333366; border-radius: 8px; background: rgba(255,255,255,0.03); color: #e0e0f0; font-size: 0.9rem; outline: none; box-sizing: border-box; }
.dialog-input:focus { border-color: #7c3aed; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }
</style>