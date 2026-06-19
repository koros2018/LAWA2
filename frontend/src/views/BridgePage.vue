<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { handleApiError, toast } from '@/utils/error'
import TypingIndicator from '@/components/TypingIndicator.vue'
import {
  getBridgePartner,
  getBridgeGreeting,
  replyBridgeGreeting,
  getBridgeLikePrompt,
  replyBridgeLike,
  getBridgeTeachPrompt,
  teachBridgeWord,
  getBridgeGroupPrompt,
  replyBridgeGroup,
  getBridgeOfflinePrompt,
  replyBridgeOffline,
  getBridgeHistory,
  getBridgeProgress,
} from '@/api/bridge'
import type {
  BridgePartner,
  BridgeGreeting,
  BridgeReply,
  BridgeLikePrompt,
  BridgeTeachPrompt,
  BridgeTeachResult,
  BridgeGroupPrompt,
  BridgeGroupResult,
  BridgeOfflinePrompt,
  BridgeOfflineResult,
  BridgeHistory,
  BridgeProgress,
} from '@/api/bridge'

type BridgeStep = 'welcome' | 'greeting' | 'reply' | 'done' | 'like' | 'like-result' | 'teach' | 'teach-result' | 'group' | 'group-result' | 'offline' | 'offline-result'

const step = ref<BridgeStep>('welcome')
const activeTab = ref<'greet' | 'like' | 'teach' | 'group' | 'offline'>('greet')
const loading = ref(false)
const partner = ref<BridgePartner | null>(null)
const greeting = ref<BridgeGreeting | null>(null)
const likePrompt = ref<BridgeLikePrompt | null>(null)
const teachPrompt = ref<BridgeTeachPrompt | null>(null)
const replyResult = ref<BridgeReply | null>(null)
const teachResult = ref<BridgeTeachResult | null>(null)
const groupPrompt = ref<BridgeGroupPrompt | null>(null)
const groupResult = ref<BridgeGroupResult | null>(null)
const offlinePrompt = ref<BridgeOfflinePrompt | null>(null)
const offlineResult = ref<BridgeOfflineResult | null>(null)
const history = ref<BridgeHistory[]>([])
const progress = ref<BridgeProgress | null>(null)

const userReply = ref('')
const replying = ref(false)
const replyError = ref('')
const typing = ref(false)  // 语伴正在输入动画

// Lv.2
const likeReply = ref('')
// Lv.3
const teachWord = ref('')
const teachMeaning = ref('')
const teachExample = ref('')
// Lv.4
const groupReplyText = ref('')
// Lv.5
const offlineReplyText = ref('')

const currentLevel = computed(() => progress.value?.current_level ?? 0)
const levels = computed(() => progress.value?.levels ?? [])

onMounted(async () => {
  loading.value = true
  try {
    const [p, h, pr] = await Promise.all([
      getBridgePartner(),
      getBridgeHistory(),
      getBridgeProgress(),
    ])
    partner.value = p
    history.value = h
    progress.value = pr
    if (h.length > 0) step.value = 'done'
    if (pr.current_level >= 2) activeTab.value = 'like'
    if (pr.current_level >= 3) activeTab.value = 'teach'
    if (pr.current_level >= 4) activeTab.value = 'group'
    if (pr.current_level >= 5) activeTab.value = 'offline'
  } catch (e) {
    handleApiError(e, '加载桥梁数据失败 · Load failed', 'Failed to load bridge data')
  } finally {
    loading.value = false
  }
})

async function startBridge() {
  loading.value = true
  try {
    const g = await getBridgeGreeting()
    greeting.value = g
    step.value = 'greeting'
  } catch (e) {
    handleApiError(e, '加载问候失败 · Load failed', 'Failed to load greeting')
  } finally {
    loading.value = false
  }
}

async function sendReply() {
  if (!userReply.value.trim() || !greeting.value || replying.value) return
  replyError.value = ''
  replying.value = true
  typing.value = true  // 显示输入动画
  try {
    const result = await replyBridgeGreeting(greeting.value.interaction_id, userReply.value)
    typing.value = false
    replyResult.value = result
    step.value = 'reply'
    userReply.value = ''
    const [h, pr] = await Promise.all([getBridgeHistory(), getBridgeProgress()])
    history.value = h
    progress.value = pr
  } catch (e: any) {
    typing.value = false
    replyError.value = e.message || '发送失败 · Send failed'
    handleApiError(e, '发送失败 · Send failed', 'Failed to send reply')
  } finally {
    replying.value = false
  }
}

async function newGreeting() {
  greeting.value = null
  replyResult.value = null
  step.value = 'welcome'
  await startBridge()
}

// ── Lv.2 点赞桥 ──

async function startLike() {
  loading.value = true
  try {
    const p = await getBridgeLikePrompt()
    likePrompt.value = p
    step.value = 'like'
  } catch (e) {
    handleApiError(e, '加载点赞提示失败 · Load failed', 'Failed to load like prompt')
  } finally {
    loading.value = false
  }
}

async function sendLike() {
  if (!likeReply.value.trim() || !likePrompt.value || replying.value) return
  replyError.value = ''
  replying.value = true
  typing.value = true
  try {
    const result = await replyBridgeLike(likePrompt.value.interaction_id, likeReply.value)
    replyResult.value = result
    step.value = 'like-result'
    likeReply.value = ''
    const [h, pr] = await Promise.all([getBridgeHistory(), getBridgeProgress()])
    history.value = h
    progress.value = pr
  } catch (e: any) {
    typing.value = false
    replyError.value = e.message || '发送失败 · Send failed'
    handleApiError(e, '发送失败 · Send failed', 'Failed to send like')
  } finally {
    replying.value = false
  }
}

async function newLike() {
  likePrompt.value = null
  replyResult.value = null
  step.value = 'welcome'
  await startLike()
}

// ── Lv.3 梗桥 ──

async function startTeach() {
  loading.value = true
  try {
    const p = await getBridgeTeachPrompt()
    teachPrompt.value = p
    step.value = 'teach'
  } catch (e) {
    handleApiError(e, '加载教梗提示失败 · Load failed', 'Failed to load teach prompt')
  } finally {
    loading.value = false
  }
}

async function sendTeach() {
  if (!teachWord.value.trim() || !teachMeaning.value.trim() || !teachPrompt.value || replying.value) return
  replyError.value = ''
  replying.value = true
  typing.value = true
  try {
    const result = await teachBridgeWord(
      teachPrompt.value.interaction_id,
      teachWord.value.trim(),
      teachMeaning.value.trim(),
      teachExample.value.trim(),
    )
    teachResult.value = result
    step.value = 'teach-result'
    teachWord.value = ''
    teachMeaning.value = ''
    teachExample.value = ''
    const [h, pr] = await Promise.all([getBridgeHistory(), getBridgeProgress()])
    history.value = h
    progress.value = pr
  } catch (e: any) {
    typing.value = false
    replyError.value = e.message || '发送失败 · Send failed'
    handleApiError(e, '发送失败 · Send failed', 'Failed to teach word')
  } finally {
    replying.value = false
  }
}

async function newTeach() {
  teachPrompt.value = null
  teachResult.value = null
  step.value = 'welcome'
  await startTeach()
}

// ── Lv.4 群聊桥 ──

async function startGroup() {
  loading.value = true
  try {
    const p = await getBridgeGroupPrompt()
    groupPrompt.value = p
    step.value = 'group'
  } catch (e) {
    handleApiError(e, '加载群聊提示失败 · Load failed', 'Failed to load group prompt')
  } finally {
    loading.value = false
  }
}

async function sendGroupReply() {
  if (!groupReplyText.value.trim() || !groupPrompt.value || replying.value) return
  replyError.value = ''
  replying.value = true
  typing.value = true
  try {
    const result = await replyBridgeGroup(groupPrompt.value.interaction_id, groupReplyText.value)
    groupResult.value = result
    step.value = 'group-result'
    groupReplyText.value = ''
    const [h, pr] = await Promise.all([getBridgeHistory(), getBridgeProgress()])
    history.value = h
    progress.value = pr
  } catch (e: any) {
    typing.value = false
    replyError.value = e.message || '发送失败 · Send failed'
    handleApiError(e, '发送失败 · Send failed', 'Failed to send group reply')
  } finally {
    replying.value = false
  }
}

async function newGroup() {
  groupPrompt.value = null
  groupResult.value = null
  step.value = 'welcome'
  await startGroup()
}

// ── Lv.5 线下桥 ──

async function startOffline() {
  loading.value = true
  try {
    const p = await getBridgeOfflinePrompt()
    offlinePrompt.value = p
    step.value = 'offline'
  } catch (e) {
    handleApiError(e, '加载线下场景失败 · Load failed', 'Failed to load offline scene')
  } finally {
    loading.value = false
  }
}

async function sendOfflineReply() {
  if (!offlineReplyText.value.trim() || !offlinePrompt.value || replying.value) return
  replyError.value = ''
  replying.value = true
  typing.value = true
  try {
    const result = await replyBridgeOffline(offlinePrompt.value.interaction_id, offlineReplyText.value)
    offlineResult.value = result
    step.value = 'offline-result'
    offlineReplyText.value = ''
    const [h, pr] = await Promise.all([getBridgeHistory(), getBridgeProgress()])
    history.value = h
    progress.value = pr
  } catch (e: any) {
    typing.value = false
    replyError.value = e.message || '发送失败 · Send failed'
    handleApiError(e, '发送失败 · Send failed', 'Failed to respond')
  } finally {
    replying.value = false
  }
}

async function newOffline() {
  offlinePrompt.value = null
  offlineResult.value = null
  step.value = 'welcome'
  await startOffline()
}

function goBackToHistory() {
  step.value = 'done'
}
</script>

<template>
  <div class="page">
    <div class="bg-glow bg-glow-3"></div>
    <section class="hero-section bridge-hero">
      <h1 class="hero-title bridge-title">双向桥梁 · Bridge</h1>
      <p class="hero-subtitle">🌉 跨越语言的遇见<br/>和语伴来一次真实的社交预演</p>
      <p class="hero-subtitle-en">Across languages, one bridge at a time</p>
    </section>

    <div v-if="loading" class="card">
      <div class="skeleton" style="height:1rem;width:6rem;margin-bottom:.75rem"></div>
      <div class="skeleton" style="height:1rem;width:100%;margin-bottom:.5rem"></div>
      <div class="skeleton" style="height:1rem;width:70%"></div>
    </div>

    <div v-if="partner && !loading" class="partner-card card">
      <div class="partner-avatar">{{ partner.partner_name.split(' ')[1] || '👤' }}</div>
      <div class="partner-info">
        <h3 class="partner-name">{{ partner.partner_name }}</h3>
        <p class="partner-bio">{{ partner.bio }}</p>
      </div>
    </div>

    <div v-if="progress && !loading" class="progress-bar card">
      <div class="progress-row">
        <span>Lv.{{ progress.current_level }}/5</span>
        <span>{{ progress.total_interactions }} 次互动 · Interactions</span>
        <span>💎 {{ progress.total_xp }} XP</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: Math.min(100, (progress.total_interactions / 5) * 100) + '%' }"></div>
      </div>
      <p class="progress-hint">{{ progress.next_level_at }}</p>
    </div>

    <template v-if="step === 'welcome' && !loading">
      <!-- 等级选择 Tab -->
      <div class="bridge-tabs">
        <button class="bt-tab" :class="{ active: activeTab === 'greet' }" @click="activeTab = 'greet'">
          <span class="bt-emoji">👋</span>
          <span class="bt-label">Lv.1 问候 · Greet</span>
          <span class="bt-status" :class="{ done: levels[0]?.done }">{{ levels[0]?.done ? '✅' : '🔒' }}</span>
        </button>
        <button class="bt-tab" :class="{ active: activeTab === 'like' }" @click="activeTab = 'like'">
          <span class="bt-emoji">👍</span>
          <span class="bt-label">Lv.2 点赞 · Like</span>
          <span class="bt-status" :class="{ done: levels[1]?.done }">{{ levels[1]?.unlocked ? (levels[1]?.done ? '✅' : '🔓') : '🔒' }}</span>
        </button>
        <button class="bt-tab" :class="{ active: activeTab === 'teach' }" @click="activeTab = 'teach'">
          <span class="bt-emoji">📖</span>
          <span class="bt-label">Lv.3 教梗 · Teach</span>
          <span class="bt-status" :class="{ done: levels[2]?.done }">{{ levels[2]?.unlocked ? (levels[2]?.done ? '✅' : '🔓') : '🔒' }}</span>
        </button>
        <button class="bt-tab" :class="{ active: activeTab === 'group' }" @click="activeTab = 'group'">
          <span class="bt-emoji">👥</span>
          <span class="bt-label">Lv.4 群聊 · Group</span>
          <span class="bt-status" :class="{ done: levels[3]?.done }">{{ levels[3]?.unlocked ? (levels[3]?.done ? '✅' : '🔓') : '🔒' }}</span>
        </button>
        <button class="bt-tab" :class="{ active: activeTab === 'offline' }" @click="activeTab = 'offline'">
          <span class="bt-emoji">🏪</span>
          <span class="bt-label">Lv.5 线下 · Offline</span>
          <span class="bt-status" :class="{ done: levels[4]?.done }">{{ levels[4]?.unlocked ? (levels[4]?.done ? '✅' : '🔓') : '🔒' }}</span>
        </button>
      </div>

      <template v-if="activeTab === 'greet'">
        <div class="bridge-start card">
          <div class="start-icon">👋</div>
          <h2 class="start-title">问候 · Greet · Lv.1</h2>
          <p class="start-desc">你的语伴正在等待你的问候。<br/>点击开始，TA 会先跟你打招呼！</p>
          <p class="start-desc-en">Your partner is waiting to say hi. Start a greeting!</p>
          <button class="btn btn-primary" @click="startBridge">🚀 开始问候 · Start</button>
        </div>
      </template>

      <template v-if="activeTab === 'like'">
        <div class="bridge-start card">
          <div class="start-icon">👍</div>
          <h2 class="start-title">点赞 · Like · Lv.2</h2>
          <p class="start-desc" v-if="!levels[1]?.unlocked">需要完成至少 3 次互动才能解锁点赞桥</p>
          <p class="start-desc" v-else>语伴分享了一条内容给你。<br/>看完后发表你的看法吧！</p>
          <p class="start-desc-en" v-if="levels[1]?.unlocked">Your partner shared something. Share your thoughts!</p>
          <button class="btn btn-primary" :disabled="!levels[1]?.unlocked" @click="startLike">👍 开始点赞 · Like</button>
        </div>
      </template>

      <template v-if="activeTab === 'teach'">
        <div class="bridge-start card">
          <div class="start-icon">📖</div>
          <h2 class="start-title">教梗 · Teach · Lv.3</h2>
          <p class="start-desc" v-if="!levels[2]?.unlocked">需要完成至少 6 次互动才能解锁梗桥</p>
          <p class="start-desc" v-else>语伴想学一个你会的词！<br/>教 TA 一个地道的网络用语吧 😎</p>
          <p class="start-desc-en" v-if="levels[2]?.unlocked">Your partner wants to learn a cool word from you!</p>
          <button class="btn btn-primary" :disabled="!levels[2]?.unlocked" @click="startTeach">📖 开始教梗 · Teach</button>
        </div>
      </template>

      <template v-if="activeTab === 'group'">
        <div class="bridge-start card">
          <div class="start-icon">👥</div>
          <h2 class="start-title">群聊 · Group · Lv.4</h2>
          <p class="start-desc" v-if="!levels[3]?.unlocked">需要完成至少 10 次互动才能解锁群聊桥</p>
          <p class="start-desc" v-else>你的语伴把你拉进了一个群聊！<br/>看看大家在聊什么，参与进去吧 🗣️</p>
          <p class="start-desc-en" v-if="levels[3]?.unlocked">Your partner added you to a group chat! Join the conversation!</p>
          <button class="btn btn-primary" :disabled="!levels[3]?.unlocked" @click="startGroup">👥 进入群聊 · Join Group</button>
        </div>
      </template>

      <template v-if="activeTab === 'offline'">
        <div class="bridge-start card">
          <div class="start-icon">🏪</div>
          <h2 class="start-title">线下 · Offline · Lv.5</h2>
          <p class="start-desc" v-if="!levels[4]?.unlocked">需要完成至少 15 次互动才能解锁线下桥</p>
          <p class="start-desc" v-else>模拟一个真实场景！<br/>咖啡店、机场、便利店……用目标语言应对吧 💪</p>
          <p class="start-desc-en" v-if="levels[4]?.unlocked">Real-life scenarios! Coffee shop, airport, convenience store… handle it!</p>
          <button class="btn btn-primary" :disabled="!levels[4]?.unlocked" @click="startOffline">🏪 开始场景 · Start Scene</button>
        </div>
      </template>
    </template>

    <template v-if="step === 'greeting' && greeting">
      <TypingIndicator v-if="typing" />
      <div class="greeting-card card">
        <div class="greeting-header">
          <span class="greeting-from">{{ greeting.partner_name }}</span>
          <span class="greeting-context">{{ greeting.context }}</span>
        </div>
        <div class="greeting-bubble">
          <p class="greeting-text">{{ greeting.greeting }}</p>
        </div>
        <details class="greeting-translation">
          <summary>🔍 翻译 · Translation</summary>
          <p class="greeting-native">{{ greeting.translation }}</p>
        </details>
        <div class="reply-section">
          <label class="reply-label">你的回复</label>
          <textarea v-model="userReply" class="reply-input" rows="3" placeholder="用你学的语言回复TA吧..." :disabled="replying"></textarea>
          <p v-if="replyError" class="reply-error">{{ replyError }}</p>
          <button class="btn btn-primary" :disabled="!userReply.trim() || replying" @click="sendReply">{{ replying ? '发送中...' : '✉️ 发送回复' }}</button>
        </div>
      </div>
    </template>

    <template v-if="step === 'reply' && replyResult">
      <div class="reply-result card">
        <div class="result-badge">🎉 回复已送达 · Reply Delivered</div>
        <div class="result-section">
          <span class="result-label">你的回复 · Your Reply</span>
          <div class="result-bubble">{{ replyResult.your_reply }}</div>
          <p v-if="replyResult.polished !== replyResult.your_reply" class="result-polish">✨ 润色建议 · Polished：{{ replyResult.polished }}</p>
        </div>
        <div class="result-section">
          <span class="result-label">{{ greeting?.partner_name }} 的回复</span>
          <div class="result-bubble partner">{{ replyResult.partner_reply }}</div>
        </div>
        <div class="result-xp">💎 +{{ replyResult.xp_earned }} XP</div>
        <div class="result-actions">
          <button class="btn btn-outline" @click="goBackToHistory">📜 查看历史 · History</button>
          <button class="btn btn-primary" @click="newGreeting">🔄 再来一次 · Again</button>
        </div>
      </div>
    </template>

    <!-- Lv.2 点赞桥 — 语伴分享 -->
    <template v-if="step === 'like' && likePrompt">
      <TypingIndicator v-if="typing" />
      <div class="greeting-card card">
        <div class="greeting-header">
          <span class="greeting-from">{{ likePrompt.partner_name }} <span class="lv-badge">Lv.2</span></span>
          <span class="greeting-context">{{ likePrompt.context }}</span>
        </div>
        <div class="greeting-bubble">
          <p class="greeting-text">{{ likePrompt.message }}</p>
        </div>
        <details class="greeting-translation">
          <summary>🔍 翻译 · Translation</summary>
          <p class="greeting-native">{{ likePrompt.translation }}</p>
        </details>
        <div class="reply-section">
          <label class="reply-label">你的看法 · Your Thoughts</label>
          <textarea v-model="likeReply" class="reply-input" rows="3" placeholder="用你学的语言说说你的想法..." :disabled="replying"></textarea>
          <p v-if="replyError" class="reply-error">{{ replyError }}</p>
          <button class="btn btn-primary" :disabled="!likeReply.trim() || replying" @click="sendLike">{{ replying ? '发送中...' : '👍 点赞 + 评论 · Like & Comment' }}</button>
        </div>
      </div>
    </template>

    <!-- Lv.2 点赞结果 -->
    <template v-if="step === 'like-result' && replyResult">
      <div class="reply-result card">
        <div class="result-badge">👍 评价已送达 · Feedback Sent</div>
        <div class="result-section">
          <span class="result-label">你的评论 · Your Comment</span>
          <div class="result-bubble">{{ replyResult.your_reply }}</div>
        </div>
        <div class="result-section">
          <span class="result-label">{{ likePrompt?.partner_name }} 的回复 · Reply</span>
          <div class="result-bubble partner">{{ replyResult.partner_reply }}</div>
        </div>
        <div class="result-xp">💎 +{{ replyResult.xp_earned }} XP</div>
        <div class="result-actions">
          <button class="btn btn-outline" @click="goBackToHistory">📜 查看历史 · History</button>
          <button class="btn btn-primary" @click="newLike">🔄 再来一条 · Another</button>
        </div>
      </div>
    </template>

    <!-- Lv.3 梗桥 — 教语伴一个词 -->
    <template v-if="step === 'teach' && teachPrompt">
      <TypingIndicator v-if="typing" />
      <div class="greeting-card card">
        <div class="greeting-header">
          <span class="greeting-from">{{ teachPrompt.partner_name }} <span class="lv-badge">Lv.3</span></span>
          <span class="greeting-context">{{ teachPrompt.context }}</span>
        </div>
        <div class="greeting-bubble">
          <p class="greeting-text">{{ teachPrompt.message }}</p>
        </div>
        <details class="greeting-translation">
          <summary>🔍 翻译 · Translation</summary>
          <p class="greeting-native">{{ teachPrompt.translation }}</p>
        </details>
        <div class="teach-section">
          <div class="reply-section">
            <label class="reply-label">📝 教TA一个词</label>
            <input v-model="teachWord" class="teach-input" placeholder="例：破防了" :disabled="replying" />
          </div>
          <div class="reply-section">
            <label class="reply-label">💡 什么意思</label>
            <input v-model="teachMeaning" class="teach-input" placeholder="用语伴的语言解释..." :disabled="replying" />
          </div>
          <div class="reply-section">
            <label class="reply-label">📎 例句（可选）</label>
            <input v-model="teachExample" class="teach-input" placeholder="展示这个词怎么用..." :disabled="replying" />
          </div>
          <p v-if="replyError" class="reply-error">{{ replyError }}</p>
          <button class="btn btn-primary" :disabled="!teachWord.trim() || !teachMeaning.trim() || replying" @click="sendTeach">{{ replying ? '发送中...' : '📖 教TA这个词' }}</button>
        </div>
      </div>
    </template>

    <!-- Lv.4 群聊桥 -->
    <template v-if="step === 'group' && groupPrompt">
      <TypingIndicator v-if="typing" />
      <div class="greeting-card card">
        <div class="greeting-header">
          <span class="greeting-from">👥 {{ groupPrompt.scene }}</span>
          <span class="greeting-context">{{ groupPrompt.context }}</span>
        </div>
        <div class="group-members">
          <span v-for="m in groupPrompt.members" :key="m.name" class="group-member-tag">{{ m.name }}</span>
        </div>
        <div class="group-chat">
          <div v-for="msg in groupPrompt.initial_messages" :key="msg.from + msg.text" class="group-msg">
            <span class="group-msg-from">{{ msg.from }}:</span>
            <span class="group-msg-text">{{ msg.text }}</span>
          </div>
          <div class="group-msg group-msg-you">
            <span class="group-msg-from">你 · You:</span>
            <span class="group-msg-text group-msg-text-you" v-if="groupReplyText">{{ groupReplyText }}</span>
            <span class="group-msg-text group-msg-text-placeholder" v-else>输入你的发言...</span>
          </div>
        </div>
        <div class="reply-section">
          <label class="reply-label">💬 你的发言 · Your Message</label>
          <textarea v-model="groupReplyText" class="reply-input" rows="2" placeholder="用目标语言在群里说点什么吧..." :disabled="replying"></textarea>
          <p v-if="replyError" class="reply-error">{{ replyError }}</p>
          <button class="btn btn-primary" :disabled="!groupReplyText.trim() || replying" @click="sendGroupReply">{{ replying ? '发送中...' : '📤 发送到群里 · Send to Group' }}</button>
        </div>
      </div>
    </template>

    <!-- Lv.4 群聊结果 -->
    <template v-if="step === 'group-result' && groupResult">
      <div class="reply-result card">
        <div class="result-badge">👥 群聊已回复 · Group Replied!</div>
        <div class="result-section">
          <span class="result-label">你的发言 · Your Message</span>
          <div class="result-bubble">{{ groupResult.your_reply }}</div>
        </div>
        <div class="result-section">
          <span class="result-label">💬 群友回复 · Group Replies</span>
          <div class="group-chat">
            <div v-for="r in groupResult.group_replies" :key="r.from + r.text" class="group-msg">
              <span class="group-msg-from">{{ r.from }}:</span>
              <span class="group-msg-text">{{ r.text }}</span>
            </div>
          </div>
        </div>
        <div class="result-xp">💎 +{{ groupResult.xp_earned }} XP</div>
        <div class="result-actions">
          <button class="btn btn-outline" @click="goBackToHistory">📜 查看历史 · History</button>
          <button class="btn btn-primary" @click="newGroup">🔄 换个群聊 · Another Group</button>
        </div>
      </div>
    </template>

    <!-- Lv.5 线下桥 -->
    <template v-if="step === 'offline' && offlinePrompt">
      <TypingIndicator v-if="typing" />
      <div class="greeting-card card">
        <div class="greeting-header">
          <span class="greeting-from">🏪 {{ offlinePrompt.scene }}</span>
          <span class="greeting-context">{{ offlinePrompt.context }}</span>
        </div>
        <div class="offline-npc">
          <span class="offline-npc-avatar">{{ offlinePrompt.npc.role === '咖啡师' || offlinePrompt.npc.role === 'Barista' ? '☕' : '👤' }}</span>
          <div class="offline-npc-info">
            <span class="offline-npc-name">{{ offlinePrompt.npc.name }}</span>
            <span class="offline-npc-role">{{ offlinePrompt.npc.role }}</span>
          </div>
        </div>
        <div class="greeting-bubble">
          <p class="greeting-text">{{ offlinePrompt.initial_message }}</p>
        </div>
        <div class="reply-section">
          <label class="reply-label">💬 你的回答 · Your Response</label>
          <textarea v-model="offlineReplyText" class="reply-input" rows="3" placeholder="用目标语言回应这个场景..." :disabled="replying"></textarea>
          <p v-if="replyError" class="reply-error">{{ replyError }}</p>
          <button class="btn btn-primary" :disabled="!offlineReplyText.trim() || replying" @click="sendOfflineReply">{{ replying ? '发送中...' : '📤 回应 · Respond' }}</button>
        </div>
      </div>
    </template>

    <!-- Lv.5 线下桥结果 -->
    <template v-if="step === 'offline-result' && offlineResult">
      <div class="reply-result card">
        <div class="result-badge">🎭 场景对话完成 · Scene Complete!</div>
        <div class="result-section">
          <span class="result-label">你的回答 · Your Response</span>
          <div class="result-bubble">{{ offlineResult.your_reply }}</div>
        </div>
        <div class="result-section">
          <span class="result-label">🎭 NPC 回复 · NPC Reply</span>
          <div class="result-bubble partner" style="white-space:pre-line">{{ offlineResult.full_reply }}</div>
        </div>
        <div class="result-xp">💎 +{{ offlineResult.xp_earned }} XP</div>
        <div class="result-actions">
          <button class="btn btn-outline" @click="goBackToHistory">📜 查看历史 · History</button>
          <button class="btn btn-primary" @click="newOffline">🔄 换个场景 · Another Scene</button>
        </div>
      </div>
    </template>

    <!-- Lv.3 教梗结果 -->
    <template v-if="step === 'teach-result' && teachResult">
      <div class="reply-result card">
        <div class="result-badge">🎓 教学成功 · Lesson Complete!</div>
        <div class="result-section">
          <span class="result-label">你教了TA · You taught：「{{ teachResult.word }}」</span>
          <div class="result-bubble">{{ teachResult.meaning }}</div>
        </div>
        <div class="result-section">
          <span class="result-label">🤔 TA 很好奇 · Curious</span>
          <div class="result-bubble partner">{{ teachResult.partner_curious }}</div>
        </div>
        <div class="result-section">
          <span class="result-label">😎 TA 试着用 · Tries it</span>
          <div class="result-bubble partner">{{ teachResult.partner_try_use }}</div>
        </div>
        <div class="result-section">
          <span class="result-label">🙏 TA 感谢你 · Grateful</span>
          <div class="result-bubble partner">{{ teachResult.partner_thanks }}</div>
        </div>
        <div class="result-xp">💎 +{{ teachResult.xp_earned }} XP</div>
        <div class="result-actions">
          <button class="btn btn-outline" @click="goBackToHistory">📜 查看历史 · History</button>
          <button class="btn btn-primary" @click="newTeach">🔄 再教一个 · Teach More</button>
        </div>
      </div>
    </template>

    <template v-if="step === 'done' && !loading">
      <div v-if="history.length === 0" class="empty-state">
        <p class="empty-icon">🌉</p>
        <p>还没有桥梁互动记录</p>
        <button class="btn btn-primary" @click="startBridge">开始桥梁</button>
      </div>
      <div v-else class="history-list">
        <div v-for="item in history" :key="item.id" class="history-item card">
          <div class="history-meta">
            <span class="history-level">Lv.{{ item.level }}</span>
            <span class="history-xp">💎 +{{ item.xp_earned }}</span>
            <span class="history-date">{{ item.created_at.slice(0,10) }}</span>
          </div>
          <div class="history-msg">
            <span class="history-direction">{{ item.direction === 'receive' ? '📩 收到 · Received' : '📤 发送 · Sent' }}</span>
            <p class="history-text">{{ item.learn_text }}</p>
          </div>
          <div v-if="item.partner_reply" class="history-reply">
            <span class="history-direction">💬 语伴回复 · Partner Reply</span>
            <p class="history-text">{{ item.partner_reply }}</p>
          </div>
        </div>
        <button class="btn btn-primary" @click="startBridge" style="margin-top:var(--space-lg)">🌉 新的桥梁互动</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.bridge-hero { padding-bottom: var(--space-xl); }
.bridge-title { font-size: var(--fs-title); }
.partner-card { display: flex; align-items: flex-start; gap: var(--space-md); margin-bottom: var(--space-lg); border-color: rgba(167,139,250,0.2); }
.partner-avatar { width: 44px; height: 44px; border-radius: 50%; background: var(--accent-glow); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; }
.partner-name { font-size: var(--fs-body); font-weight: var(--fw-semibold); color: var(--text-primary); }
.partner-bio { font-size: var(--fs-caption); color: var(--text-tertiary); margin-top: 2px; line-height: 1.5; }
.progress-bar { margin-bottom: var(--space-lg); }
.progress-row { display: flex; justify-content: space-between; font-size: var(--fs-caption); color: var(--text-tertiary); margin-bottom: var(--space-sm); gap: var(--space-sm); flex-wrap: wrap; }
.progress-track { height: 4px; background: var(--bg-primary); border-radius: 2px; overflow: hidden; margin-bottom: var(--space-xs); }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), #34d399); border-radius: 2px; transition: width var(--duration-slow) var(--ease-out); }
.progress-hint { font-size: var(--fs-small); color: var(--text-tertiary); }
.bridge-start { text-align: center; padding: var(--space-2xl) var(--space-lg); display: flex; flex-direction: column; align-items: center; gap: var(--space-lg); }
.start-icon { font-size: 3rem; }
.start-title { font-size: var(--fs-subtitle); font-weight: var(--fw-bold); color: var(--text-primary); }
.start-desc { font-size: var(--fs-body); color: var(--text-secondary); line-height: 1.7; }
.greeting-card { margin-bottom: var(--space-lg); }
.greeting-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); gap: var(--space-sm); flex-wrap: wrap; }
.greeting-from { font-size: var(--fs-caption); color: var(--accent); font-weight: var(--fw-medium); }
.greeting-context { font-size: var(--fs-small); color: var(--text-tertiary); }
.greeting-bubble { background: var(--accent-glow); border: 1px solid rgba(167,139,250,0.2); border-radius: 12px; padding: var(--space-md); margin-bottom: var(--space-sm); }
.greeting-text { font-size: var(--fs-body); line-height: 1.7; color: var(--text-primary); }
.greeting-translation { font-size: var(--fs-small); color: var(--text-tertiary); margin-bottom: var(--space-lg); cursor: pointer; }
.greeting-translation summary { margin-bottom: var(--space-xs); }
.greeting-native { font-size: var(--fs-caption); color: var(--text-secondary); line-height: 1.6; padding: var(--space-sm); background: var(--surface); border-radius: var(--radius-sm); }
.reply-section { display: flex; flex-direction: column; gap: var(--space-sm); }
.reply-label { font-size: var(--fs-caption); color: var(--text-tertiary); }
.reply-input { width: 100%; background: var(--surface); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: var(--space-md); color: var(--text-primary); font-size: var(--fs-body); resize: vertical; font-family: inherit; transition: border-color var(--duration-normal); }
.reply-input:focus { outline: none; border-color: var(--accent); }
.reply-input:disabled { opacity: .5; }
.reply-error { font-size: var(--fs-small); color: #f87171; }
.reply-result { margin-bottom: var(--space-lg); }
.result-badge { font-size: var(--fs-subtitle); font-weight: var(--fw-bold); color: var(--success); text-align: center; margin-bottom: var(--space-lg); }
.result-section { margin-bottom: var(--space-lg); }
.result-label { display: block; font-size: var(--fs-small); color: var(--text-tertiary); margin-bottom: var(--space-xs); }
.result-bubble { background: var(--surface); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: var(--space-md); font-size: var(--fs-body); line-height: 1.6; color: var(--text-primary); }
.result-bubble.partner { background: var(--accent-glow); border-color: rgba(167,139,250,0.2); }
.result-polish { font-size: var(--fs-small); color: var(--accent); margin-top: var(--space-xs); }
.result-xp { text-align: center; font-size: var(--fs-subtitle); font-weight: var(--fw-bold); color: var(--success); margin-bottom: var(--space-lg); }
.result-actions { display: flex; gap: var(--space-sm); flex-wrap: wrap; justify-content: center; }
.history-list { display: flex; flex-direction: column; gap: var(--space-md); margin-bottom: var(--space-lg); }
.history-item { border-color: rgba(255,255,255,0.06); }
.history-meta { display: flex; gap: var(--space-sm); align-items: center; margin-bottom: var(--space-sm); flex-wrap: wrap; }
.history-level { font-size: var(--fs-small); color: var(--accent); background: var(--accent-glow); padding: 1px 6px; border-radius: 4px; }
.history-xp { font-size: var(--fs-small); color: var(--success); }
.history-date { font-size: var(--fs-small); color: var(--text-tertiary); margin-left: auto; }
.history-msg, .history-reply { margin-bottom: var(--space-sm); }
.history-direction { display: block; font-size: var(--fs-small); color: var(--text-tertiary); margin-bottom: 2px; }
.history-text { font-size: var(--fs-caption); line-height: 1.6; color: var(--text-secondary); word-break: break-word; }
.empty-state { text-align: center; padding: var(--space-3xl) 0; display: flex; flex-direction: column; align-items: center; gap: var(--space-lg); color: var(--text-tertiary); }
.bridge-tabs { display: flex; gap: var(--space-sm); margin-bottom: var(--space-lg); flex-wrap: wrap; }
.bt-tab { flex: 1; min-width: 0; display: flex; align-items: center; gap: var(--space-xs); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid rgba(255,255,255,0.06); background: var(--bg-card); color: var(--text-tertiary); cursor: pointer; transition: all var(--duration-normal); text-align: left; font-size: var(--fs-small); font-family: inherit; }
.bt-tab.active { border-color: var(--accent); color: var(--text-primary); background: var(--accent-glow); }
.bt-emoji { font-size: 1rem; flex-shrink: 0; }
.bt-label { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bt-status { flex-shrink: 0; font-size: var(--fs-caption); }
.bt-status.done { color: var(--success); }
.lv-badge { font-size: var(--fs-small); background: var(--accent-glow); padding: 1px 6px; border-radius: 4px; margin-left: var(--space-xs); color: var(--accent); }
.group-members { display: flex; gap: var(--space-xs); flex-wrap: wrap; margin-bottom: var(--space-md); }
.group-member-tag { font-size: var(--fs-small); background: var(--accent-glow); padding: 2px 8px; border-radius: 12px; color: var(--accent); }
.group-chat { display: flex; flex-direction: column; gap: var(--space-xs); margin-bottom: var(--space-md); background: var(--surface); border-radius: var(--radius-sm); padding: var(--space-md); }
.group-msg { display: flex; gap: var(--space-xs); align-items: flex-start; }
.group-msg-from { font-size: var(--fs-small); color: var(--accent); font-weight: var(--fw-medium); white-space: nowrap; }
.group-msg-text { font-size: var(--fs-caption); color: var(--text-secondary); line-height: 1.5; }
.group-msg-you { margin-top: var(--space-xs); padding-top: var(--space-xs); border-top: 1px solid rgba(255,255,255,0.06); }
.group-msg-text-you { color: var(--text-primary); }
.group-msg-text-placeholder { color: var(--text-tertiary); font-style: italic; }
.offline-npc { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md); }
.offline-npc-avatar { font-size: 1.5rem; }
.offline-npc-info { display: flex; flex-direction: column; gap: 2px; }
.offline-npc-name { font-size: var(--fs-body); font-weight: var(--fw-medium); color: var(--text-primary); }
.offline-npc-role { font-size: var(--fs-small); color: var(--text-tertiary); }
.teach-section { display: flex; flex-direction: column; gap: var(--space-md); }
.teach-input { width: 100%; background: var(--surface); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: var(--space-sm) var(--space-md); color: var(--text-primary); font-size: var(--fs-body); font-family: inherit; transition: border-color var(--duration-normal); }
.teach-input:focus { outline: none; border-color: var(--accent); }
.teach-input:disabled { opacity: .5; }
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(167, 139, 250, 0.08);
  border-radius: 0.75rem;
  color: #a78bfa;
  font-size: 0.8rem;
  margin-bottom: var(--space-md);
}

.typing-dots {
  display: flex;
  gap: 0.15rem;
  align-items: center;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a78bfa;
  opacity: 0.3;
  transition: opacity 0.3s;
}

.typing-dot.active {
  opacity: 1;
}

.empty-icon { font-size: 3rem; }
@media (max-width:374px) { .greeting-bubble { padding: var(--space-sm); } .result-bubble { padding: var(--space-sm); } }
</style>