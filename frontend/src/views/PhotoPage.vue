<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { session } from '@/store/session'
import {
  uploadPhoto,
  getPhotoDetail,
  getPhotoHistory,
  chatAboutPhoto,
  getPhotoChats,
  getPhotoImageUrl,
  getPhotoThumbnailUrl,
  type PhotoData,
  type PhotoChat,
  type WordItem,
} from '@/api/photo'

// ── 状态 ──
const photos = ref<PhotoData[]>([])
const currentPhoto = ref<PhotoData | null>(null)
const chats = ref<PhotoChat[]>([])
const message = ref('')
const loading = ref(false)
const uploading = ref(false)
const galleryOpen = ref(false)
const chatEndRef = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const chatMode = ref<'photo_chat' | 'free_chat'>('free_chat')
const freeChats = ref<{ role: string; content: string; content_en: string }[]>([])

const userId = computed(() => session.user?.userId || '')

// ── 加载图片历史 ──
async function loadHistory() {
  if (!userId.value) return
  try {
    photos.value = await getPhotoHistory(userId.value)
  } catch (e: any) {
    console.error('加载图片历史失败:', e)
  }
}

// ── 选中图片 ──
async function selectPhoto(photo: PhotoData) {
  currentPhoto.value = photo
  galleryOpen.value = false
  loading.value = true
  chatMode.value = 'photo_chat'
  try {
    const detail = await getPhotoDetail(photo.id, userId.value)
    currentPhoto.value = detail
    chats.value = await getPhotoChats(photo.id, userId.value)
  } catch (e: any) {
    console.error('加载图片详情失败:', e)
  } finally {
    loading.value = false
  }
}

// ── 上传图片 ──
async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !userId.value) return

  uploading.value = true
  try {
    const result = await uploadPhoto(file, userId.value)
    photos.value.unshift(result)
    await selectPhoto(result)
  } catch (e: any) {
    console.error('上传失败:', e)
    alert('Upload failed / 上传失败: ' + (e.message || 'unknown'))
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

// ── 发送对话 ──
async function sendMessage() {
  const msg = message.value.trim()
  if (!msg || !userId.value) return

  message.value = ''

  if (chatMode.value === 'photo_chat' && currentPhoto.value) {
    const tempUser: PhotoChat = {
      id: 'temp',
      role: 'user',
      content: msg,
      content_en: '',
      created_at: new Date().toISOString(),
    }
    chats.value.push(tempUser)
    try {
      const reply = await chatAboutPhoto(currentPhoto.value.id, userId.value, msg)
      chats.value.push(reply)
    } catch (e: any) {
      chats.value.push({
        id: 'error',
        role: 'assistant',
        content: '抱歉，回复失败，请稍后再试。',
        content_en: 'Sorry, failed to reply. Please try again later.',
        created_at: new Date().toISOString(),
      })
    }
  } else {
    freeChats.value.push({ role: 'user', content: msg, content_en: '' })
    try {
      const res = await fetch('/api/v2/bridge/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId.value, message: msg }),
      })
      const json = await res.json()
      if (json.status === 'ok') {
        freeChats.value.push({
          role: 'assistant',
          content: json.data.reply || json.data.content || '',
          content_en: json.data.reply_en || json.data.content_en || '',
        })
      }
    } catch (e) {
      freeChats.value.push({ role: 'assistant', content: '抱歉，回复失败。', content_en: 'Sorry, failed to reply.' })
    }
  }

  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  setTimeout(() => {
    chatEndRef.value?.scrollIntoView({ behavior: 'smooth' })
  }, 100)
}

function showWordDetail(word: WordItem) {
  alert(`${word.word}\n${word.zh} / ${word.en}\n例: ${word.example}`)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(() => { loadHistory() })
</script>

<template>
  <div class="photo-page">
    <div class="preview-area">
      <div v-if="currentPhoto" class="photo-card">
        <div class="photo-image-wrapper">
          <img v-if="currentPhoto.image_path" :src="getPhotoImageUrl(currentPhoto.id)" class="photo-img"
            :alt="currentPhoto.ai_description || currentPhoto.original_filename"
            @error="$event.target.style.display='none'" />
          <div class="photo-placeholder" v-if="!currentPhoto.image_path">
            <span class="placeholder-icon">📸</span>
            <span class="placeholder-text">{{ currentPhoto.original_filename }}</span>
            <span class="placeholder-size">{{ formatSize(currentPhoto.file_size) }}</span>
          </div>
        </div>
        <div class="photo-info">
          <div class="scene-tags">
            <span v-for="tag in currentPhoto.scene_tags" :key="tag" class="scene-tag">#{{ tag }}</span>
          </div>
          <p class="description">{{ currentPhoto.ai_description }}</p>
          <p class="description-en">{{ currentPhoto.ai_description_en }}</p>
          <div v-if="currentPhoto.extracted_words?.length" class="word-cards">
            <button v-for="(word, i) in currentPhoto.extracted_words.slice(0, 6)" :key="i" class="word-chip" @click="showWordDetail(word)">
              <span class="word-text">{{ word.word }}</span>
              <span class="word-zh">{{ word.zh }}</span>
            </button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state" @click="fileInput?.click()">
        <span class="empty-icon">📸</span>
        <p class="empty-title">拍照理解 · Photo Understanding</p>
        <p class="empty-desc">拍一张照片，AI 用中英双语和你聊</p>
        <p class="empty-desc-en">Snap a photo, AI understands and chats bilingually</p>
        <button class="upload-btn" :disabled="uploading">
          {{ uploading ? 'Uploading... 上传中...' : '📷 选择图片 · Choose Photo' }}
        </button>
      </div>
      <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="handleFileUpload" />
    </div>

    <div v-if="currentPhoto" class="chat-area">
      <div v-if="currentPhoto.extracted_words?.length" class="word-banner">
        <span class="word-banner-label">✨ 关键词 Key Words</span>
        <button v-for="(word, i) in currentPhoto.extracted_words.slice(0, 4)" :key="i" class="word-pill" @click="showWordDetail(word)">{{ word.word }}</button>
      </div>

      <div v-if="chatMode === 'photo_chat'" class="chat-messages">
        <div v-for="chat in chats" :key="chat.id" class="chat-bubble" :class="chat.role === 'user' ? 'user-bubble' : 'assistant-bubble'">
          <div class="bubble-role">{{ chat.role === 'user' ? '🧑 你 · You' : '🦝 达子 · Dazi' }}</div>
          <div class="bubble-content">{{ chat.content }}</div>
          <div v-if="chat.content_en" class="bubble-content-en">{{ chat.content_en }}</div>
        </div>
        <div ref="chatEndRef" />
      </div>

      <div v-else class="chat-messages">
        <div v-for="(chat, i) in freeChats" :key="i" class="chat-bubble" :class="chat.role === 'user' ? 'user-bubble' : 'assistant-bubble'">
          <div class="bubble-role">{{ chat.role === 'user' ? '🧑 你 · You' : '🦝 达子 · Dazi' }}</div>
          <div class="bubble-content">{{ chat.content }}</div>
          <div v-if="chat.content_en" class="bubble-content-en">{{ chat.content_en }}</div>
        </div>
        <div ref="chatEndRef" />
      </div>
    </div>

    <div v-if="currentPhoto" class="input-area">
      <div class="mode-tabs">
        <button class="mode-tab" :class="{ active: chatMode === 'photo_chat' }" @click="chatMode = 'photo_chat'">🖼 图片对话</button>
        <button class="mode-tab" :class="{ active: chatMode === 'free_chat' }" @click="chatMode = 'free_chat'">💬 自由聊天</button>
      </div>
      <div class="input-row">
        <button class="action-btn" @click="fileInput?.click()" title="Upload / 上传">📷</button>
        <button class="action-btn" @click="galleryOpen = !galleryOpen" title="Gallery / 画廊">🖼️</button>
        <input v-model="message" type="text" class="msg-input"
          :placeholder="chatMode === 'photo_chat' ? '问关于这张图的问题... Ask about this photo...' : '说点什么... Say something...'"
          @keyup.enter="sendMessage" />
        <button class="send-btn" :disabled="!message.trim()" @click="sendMessage">➤</button>
      </div>
    </div>

    <Transition name="slide-up">
      <div v-if="galleryOpen" class="gallery-drawer">
        <div class="gallery-header">
          <span>📖 图片画廊 · Photo Gallery</span>
          <button class="close-btn" @click="galleryOpen = false">✕</button>
        </div>
        <div class="gallery-grid">
          <div v-for="photo in photos" :key="photo.id" class="gallery-item"
            :class="{ active: currentPhoto?.id === photo.id }" @click="selectPhoto(photo)">
            <img v-if="photo.image_path" :src="getPhotoThumbnailUrl(photo.id)" class="gallery-thumb"
              @error="$event.target.style.display='none'" />
            <div v-else class="gallery-thumb-placeholder">📸</div>
            <div class="gallery-info">
              <span class="gallery-filename">{{ photo.original_filename }}</span>
              <span class="gallery-meta">{{ photo.scene_tags?.join(', ') }}</span>
            </div>
          </div>
          <div v-if="photos.length === 0" class="gallery-empty">
            <p>还没有照片 · No photos yet</p>
            <p class="gallery-hint">点击 📷 上传第一张</p>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.photo-page {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0a0a1a 0%, #0f0f2a 100%);
  position: relative;
}
.preview-area { padding: 1rem; padding-top: 1rem; flex-shrink: 0; }
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 3rem 1.5rem; min-height: 40dvh; cursor: pointer; border-radius: 1rem;
  border: 2px dashed rgba(255,255,255,0.08); transition: border-color 0.3s;
}
.empty-state:hover { border-color: rgba(167, 139, 250, 0.3); }
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-title {
  font-size: 1.3rem; font-weight: 600;
  background: linear-gradient(135deg, #c084fc, #818cf8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  margin-bottom: 0.5rem;
}
.empty-desc { color: var(--text-secondary, #aaa); font-size: 0.9rem; }
.empty-desc-en { color: var(--text-muted, #666); font-size: 0.85rem; font-style: italic; margin-top: 0.2rem; margin-bottom: 1.5rem; }
.upload-btn {
  background: linear-gradient(135deg, #7c3aed, #6366f1); color: white; border: none;
  padding: 0.75rem 1.5rem; border-radius: 0.75rem; font-size: 1rem; cursor: pointer; transition: opacity 0.2s;
}
.upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.photo-card { background: rgba(255,255,255,0.04); border-radius: 1rem; overflow: hidden; border: 1px solid rgba(255,255,255,0.06); }
.photo-image-wrapper { width: 100%; aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.3); overflow: hidden; border-radius: 0.75rem 0.75rem 0 0; }
.photo-img { width: 100%; height: 100%; object-fit: contain; }
.photo-placeholder { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; color: rgba(255,255,255,0.4); }
.placeholder-icon { font-size: 3rem; }
.placeholder-text { font-size: 0.9rem; }
.placeholder-size { font-size: 0.75rem; opacity: 0.6; }
.photo-info { padding: 1rem; }
.scene-tags { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
.scene-tag { background: rgba(167, 139, 250, 0.15); color: #a78bfa; padding: 0.15rem 0.5rem; border-radius: 0.5rem; font-size: 0.7rem; }
.description { color: var(--text-primary, #eee); font-size: 0.95rem; line-height: 1.5; margin-bottom: 0.3rem; }
.description-en { color: var(--text-muted, #888); font-size: 0.85rem; font-style: italic; line-height: 1.4; }
.word-cards { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.8rem; }
.word-chip {
  display: flex; flex-direction: column; align-items: center;
  background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 0.6rem; padding: 0.3rem 0.6rem; cursor: pointer; transition: background 0.2s;
}
.word-chip:hover { background: rgba(99, 102, 241, 0.2); }
.word-text { font-size: 0.85rem; color: #818cf8; font-weight: 600; }
.word-zh { font-size: 0.65rem; color: var(--text-muted, #888); }

.chat-area { flex: 1; overflow-y: auto; padding: 0 1rem 0.5rem; display: flex; flex-direction: column; }
.word-banner { display: flex; align-items: center; gap: 0.4rem; padding: 0.5rem 0; flex-wrap: wrap; flex-shrink: 0; }
.word-banner-label { font-size: 0.7rem; color: var(--text-muted, #888); }
.word-pill { background: rgba(167, 139, 250, 0.12); border: none; color: #c084fc; padding: 0.2rem 0.5rem; border-radius: 0.5rem; font-size: 0.7rem; cursor: pointer; }
.word-pill:hover { background: rgba(167, 139, 250, 0.25); }

.chat-messages { flex: 1; overflow-y: auto; padding: 0.5rem 0; display: flex; flex-direction: column; gap: 0.6rem; }
.chat-bubble { max-width: 85%; padding: 0.6rem 0.8rem; border-radius: 0.8rem; }
.user-bubble { align-self: flex-end; background: rgba(99, 102, 241, 0.15); border-bottom-right-radius: 0.2rem; }
.assistant-bubble { align-self: flex-start; background: rgba(255,255,255,0.06); border-bottom-left-radius: 0.2rem; }
.bubble-role { font-size: 0.65rem; color: var(--text-muted, #888); margin-bottom: 0.25rem; }
.bubble-content { font-size: 0.9rem; line-height: 1.5; color: var(--text-primary, #eee); }
.bubble-content-en { font-size: 0.8rem; line-height: 1.4; color: var(--text-muted, #888); font-style: italic; margin-top: 0.3rem; padding-top: 0.3rem; border-top: 1px solid rgba(255,255,255,0.06); }

/* ── 输入区 ── */
.input-area {
  flex-shrink: 0;
  padding: 0.5rem 1rem;
  padding-bottom: calc(0.5rem + env(safe-area-inset-bottom, 0px) + 4.5rem);
  background: rgba(15,15,30,0.9);
  border-top: 1px solid rgba(255,255,255,0.06);
}
.mode-tabs {
  display: flex;
  gap: 0.3rem;
  margin-bottom: 0.4rem;
}
.mode-tab {
  flex: 1;
  padding: 0.3rem 0;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 0.5rem;
  color: var(--text-muted, #888);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s;
}
.mode-tab.active {
  background: rgba(167, 139, 250, 0.15);
  border-color: rgba(167, 139, 250, 0.3);
  color: #a78bfa;
}
.input-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.action-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 0.6rem;
  padding: 0.5rem 0.5rem;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.2s;
  line-height: 1;
}
.action-btn:hover { background: rgba(255,255,255,0.1); }
.msg-input {
  flex: 1;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 0.6rem;
  padding: 0.55rem 0.75rem;
  color: white;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}
.msg-input:focus { border-color: rgba(167, 139, 250, 0.4); }
.msg-input::placeholder { color: var(--text-muted, #666); }
.send-btn {
  background: linear-gradient(135deg, #7c3aed, #6366f1);
  color: white;
  border: none;
  border-radius: 0.6rem;
  padding: 0.5rem 0.8rem;
  font-size: 1rem;
  cursor: pointer;
  transition: opacity 0.2s;
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── 画廊抽屉 ── */
.gallery-drawer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 50dvh;
  background: rgba(10,10,26,0.98);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,0.08);
  border-radius: 1rem 1rem 0 0;
  z-index: 200;
  display: flex;
  flex-direction: column;
}
.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: 0.9rem;
  color: var(--text-primary, #eee);
}
.close-btn {
  background: none;
  border: none;
  color: var(--text-muted, #888);
  font-size: 1.1rem;
  cursor: pointer;
}
.gallery-grid {
  overflow-y: auto;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.gallery-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.6rem;
  border-radius: 0.6rem;
  cursor: pointer;
  transition: background 0.2s;
}
.gallery-item:hover { background: rgba(255,255,255,0.04); }
.gallery-item.active { background: rgba(167, 139, 250, 0.12); }
.gallery-thumb-placeholder { font-size: 1.5rem; width: 2rem; height: 2rem; display: flex; align-items: center; justify-content: center; }
.gallery-thumb { width: 2rem; height: 2rem; object-fit: cover; border-radius: 0.4rem; flex-shrink: 0; }
.gallery-info { display: flex; flex-direction: column; gap: 0.1rem; }
.gallery-filename { font-size: 0.85rem; color: var(--text-primary, #eee); }
.gallery-meta { font-size: 0.7rem; color: var(--text-muted, #888); }
.gallery-empty { padding: 1.5rem; text-align: center; color: var(--text-muted, #888); }
.gallery-hint { font-size: 0.8rem; margin-top: 0.3rem; color: var(--text-muted, #666); }

/* ── 抽屉动画 ── */
.slide-up-enter-active, .slide-up-leave-active { transition: transform 0.3s ease, opacity 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); opacity: 0; }
</style>