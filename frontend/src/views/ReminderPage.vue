<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getEvents, createEvent, updateEvent, deleteEvent,
  generateGreeting,
  type ReminderEvent as ReminderEventType,
  type GreetingData,
} from '@/api/reminder'

// ── 状态 ──
const loading = ref(true)
const currentView = ref<'month' | 'day' | 'add'>('month')
const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth()) // 0-11
const events = ref<ReminderEventType[]>([])
const selectedDateEvents = ref<ReminderEventType[]>([])
const selectedDateStr = ref('')
const grettingData = ref<GreetingData | null>(null)
const grettingLoading = ref(false)
const showGreeting = ref(false)

// 编辑/删除
const editingEvent = ref<ReminderEventType | null>(null)
const showEditForm = ref(false)
const tempEvent = ref({
  title: '', titleEn: '', eventDate: '',
  eventType: 'personal', note: '', noteEn: '',
})
const savingEvent = ref(false)
const showDeleteConfirm = ref(false)
const deletingId = ref<string | null>(null)

// ── 计算 ──
const monthLabel = computed(() => {
  const months = [
    '一月 Jan', '二月 Feb', '三月 Mar', '四月 Apr',
    '五月 May', '六月 Jun', '七月 Jul', '八月 Aug',
    '九月 Sep', '十月 Oct', '十一月 Nov', '十二月 Dec',
  ]
  return `${currentYear.value} · ${months[currentMonth.value]}`
})

const calendarGrid = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startWeekday = firstDay.getDay()
  const prevLastDay = new Date(year, month, 0).getDate()
  const cells: { day: number; isCurrentMonth: boolean; isToday: boolean; dateStr: string }[] = []

  for (let i = startWeekday - 1; i >= 0; i--) {
    const d = prevLastDay - i
    cells.push({
      day: d, isCurrentMonth: false, isToday: false,
      dateStr: new Date(year, month - 1, d).toISOString().slice(0, 10),
    })
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = d === today.getDate() && month === today.getMonth() && year === today.getFullYear()
    cells.push({
      day: d, isCurrentMonth: true, isToday,
      dateStr: new Date(year, month, d).toISOString().slice(0, 10),
    })
  }

  while (cells.length < 42) {
    const d = cells.length - (startWeekday + daysInMonth) + 1
    cells.push({
      day: d, isCurrentMonth: false, isToday: false,
      dateStr: new Date(year, month + 1, d).toISOString().slice(0, 10),
    })
  }
  return cells
})

function eventsForDate(dateStr: string): ReminderEventType[] {
  return events.value.filter(e => e.event_date === dateStr)
}

// ── 方法 ──
function prevMonth() {
  if (currentMonth.value === 0) { currentMonth.value = 11; currentYear.value-- }
  else { currentMonth.value-- }
  loadEvents()
}

function nextMonth() {
  if (currentMonth.value === 11) { currentMonth.value = 0; currentYear.value++ }
  else { currentMonth.value++ }
  loadEvents()
}

function goToday() {
  currentYear.value = today.getFullYear()
  currentMonth.value = today.getMonth()
  loadEvents()
}

function selectDate(dateStr: string) {
  selectedDateStr.value = dateStr
  selectedDateEvents.value = eventsForDate(dateStr)
  currentView.value = 'day'
}

function backToMonth() {
  currentView.value = 'month'
  selectedDateStr.value = ''
  selectedDateEvents.value = []
}

function openAddForm() {
  editingEvent.value = null
  tempEvent.value = {
    title: '', titleEn: '', eventDate: selectedDateStr.value || today.toISOString().slice(0, 10),
    eventType: 'personal', note: '', noteEn: '',
  }
  currentView.value = 'add'
}

function openEditForm(e: ReminderEventType) {
  editingEvent.value = e
  tempEvent.value = {
    title: e.title, titleEn: e.title_en || '',
    eventDate: e.event_date, eventType: e.event_type,
    note: e.note || '', noteEn: e.note_en || '',
  }
  showEditForm.value = true
}

function closeEditForm() {
  showEditForm.value = false
  editingEvent.value = null
}

async function saveEvent() {
  if (!tempEvent.value.title.trim()) return
  savingEvent.value = true
  try {
    if (editingEvent.value) {
      await updateEvent(editingEvent.value.id, {
        title: tempEvent.value.title, title_en: tempEvent.value.titleEn,
        event_date: tempEvent.value.eventDate, event_type: tempEvent.value.eventType,
        note: tempEvent.value.note || null, note_en: tempEvent.value.noteEn || null,
      })
    } else {
      await createEvent({
        title: tempEvent.value.title, title_en: tempEvent.value.titleEn || undefined,
        event_date: tempEvent.value.eventDate, event_type: tempEvent.value.eventType,
        note: tempEvent.value.note || undefined, note_en: tempEvent.value.noteEn || undefined,
      })
    }
    showEditForm.value = false
    editingEvent.value = null
    currentView.value = 'month'
    await loadEvents()
  } catch (e) { console.error('Save failed', e) }
  finally { savingEvent.value = false }
}

async function doDelete(id: string) {
  try {
    await deleteEvent(id)
    showDeleteConfirm.value = false
    deletingId.value = null
    selectedDateEvents.value = selectedDateEvents.value.filter(e => e.id !== id)
    await loadEvents()
  } catch (e) { console.error('Delete failed', e) }
}

async function doGreeting(eventId: string) {
  grettingLoading.value = true
  try {
    grettingData.value = await generateGreeting(eventId)
    showGreeting.value = true
  } catch (e) { console.error('Greeting failed', e) }
  finally { grettingLoading.value = false }
}

function closeGreeting() { showGreeting.value = false; grettingData.value = null }

async function loadEvents() {
  try {
    const fd = new Date(currentYear.value, currentMonth.value, 1)
    const ld = new Date(currentYear.value, currentMonth.value + 1, 0)
    events.value = await getEvents(fd.toISOString().slice(0, 10), ld.toISOString().slice(0, 10))
  } catch (e) { console.error('Load events failed', e) }
  finally { loading.value = false }
}

function typeColor(t: string): string {
  const map: Record<string, string> = {
    holiday: '#f59e0b', anniversary: '#ec4899',
    birthday: '#f472b6', todo: '#60a5fa', personal: '#a78bfa',
  }
  return map[t] || '#a78bfa'
}

function typeLabel(t: string): string {
  const map: Record<string, string> = {
    holiday: '节日 Holiday', anniversary: '纪念日 Anniversary',
    birthday: '生日 Birthday', todo: '待办 Todo', personal: '个人 Personal',
  }
  return map[t] || t
}

onMounted(loadEvents)
</script>

<template>
  <div class="reminder-page">
    <div v-if="loading" class="loading-screen">
      <div class="spinner"></div>
      <p>Loading · 加载中</p>
    </div>

    <!-- ════ 日历月视图 ════ -->
    <template v-else-if="currentView === 'month'">
      <div class="cal-header">
        <button class="nav-btn" @click="prevMonth" aria-label="上个月">‹</button>
        <h2 class="month-title">{{ monthLabel }}</h2>
        <button class="nav-btn" @click="nextMonth" aria-label="下个月">›</button>
        <button class="today-btn" @click="goToday">今天 Today</button>
      </div>

      <div class="weekday-row">
        <span v-for="d in ['日','一','二','三','四','五','六']" :key="d" class="weekday-label">{{ d }}</span>
      </div>

      <div class="calendar-grid">
        <button
          v-for="cell in calendarGrid"
          :key="cell.dateStr"
          class="cal-day"
          :class="{ 'other-month': !cell.isCurrentMonth, 'is-today': cell.isToday, 'has-events': eventsForDate(cell.dateStr).length > 0 }"
          @click="cell.isCurrentMonth && selectDate(cell.dateStr)"
        >
          <span class="day-num">{{ cell.day }}</span>
          <div v-if="eventsForDate(cell.dateStr).length > 0" class="day-dots">
            <span v-for="evt in eventsForDate(cell.dateStr).slice(0,3)" :key="evt.id"
              class="day-dot" :style="{ background: typeColor(evt.event_type) }"></span>
          </div>
        </button>
      </div>
    </template>

    <!-- ════ 日视图 ════ -->
    <template v-else-if="currentView === 'day'">
      <div class="day-header">
        <button class="back-btn" @click="backToMonth">‹ 返回 Back</button>
        <h3 class="day-title">{{ selectedDateStr }}</h3>
        <button class="add-btn" @click="openAddForm">+ 添加 Add</button>
      </div>

      <div class="event-list">
        <div v-if="selectedDateEvents.length === 0" class="empty-state">
          <span class="empty-icon">📭</span>
          <p>没有事件 · No events</p>
          <button class="add-btn" @click="openAddForm">+ 添加 Add one</button>
        </div>

        <div v-for="evt in selectedDateEvents" :key="evt.id" class="event-card" :style="{ borderLeftColor: typeColor(evt.event_type) }">
          <div class="event-top">
            <span class="event-type-badge" :style="{ background: typeColor(evt.event_type) }">{{ typeLabel(evt.event_type) }}</span>
            <div class="event-actions">
              <button v-if="evt.event_type === 'holiday'" class="action-btn greet-btn" :disabled="grettingLoading" @click="doGreeting(evt.id)" title="祝福 Greeting">🎉</button>
              <button v-if="evt.event_type !== 'holiday'" class="action-btn" @click="openEditForm(evt)" title="编辑 Edit">✏️</button>
              <button v-if="evt.event_type !== 'holiday'" class="action-btn" @click="showDeleteConfirm = true; deletingId = evt.id" title="删除 Delete">🗑️</button>
            </div>
          </div>
          <h4 class="event-title">{{ evt.title }}</h4>
          <p class="event-title-en">{{ evt.title_en }}</p>
          <p v-if="evt.note" class="event-note">{{ evt.note }}</p>
          <p v-if="evt.note_en" class="event-note-en">{{ evt.note_en }}</p>
          <div v-if="evt.culture_background" class="culture-box">
            <p class="culture-text">{{ evt.culture_background }}</p>
            <p class="culture-text-en">{{ evt.culture_background_en }}</p>
          </div>
        </div>
      </div>
    </template>

    <!-- ════ 添加表单 ════ -->
    <template v-else-if="currentView === 'add'">
      <div class="add-header">
        <button class="back-btn" @click="backToMonth">‹ 取消 Cancel</button>
        <h3 class="add-title">新事件 · New Event</h3>
      </div>
      <div class="add-form">
        <label class="form-field"><span class="field-label">标题 Title</span><input v-model="tempEvent.title" class="form-input" placeholder="事件名称" /></label>
        <label class="form-field"><span class="field-label">英文标题 Title (EN)</span><input v-model="tempEvent.titleEn" class="form-input" placeholder="英文名称" /></label>
        <label class="form-field"><span class="field-label">日期 Date</span><input v-model="tempEvent.eventDate" type="date" class="form-input" /></label>
        <label class="form-field">
          <span class="field-label">类型 Type</span>
          <select v-model="tempEvent.eventType" class="form-select">
            <option value="personal">个人 · Personal</option>
            <option value="todo">待办 · Todo</option>
            <option value="anniversary">纪念日 · Anniversary</option>
            <option value="birthday">生日 · Birthday</option>
          </select>
        </label>
        <label class="form-field"><span class="field-label">备注 Note</span><textarea v-model="tempEvent.note" class="form-textarea" placeholder="备注"></textarea></label>
        <label class="form-field"><span class="field-label">英文备注 Note (EN)</span><textarea v-model="tempEvent.noteEn" class="form-textarea" placeholder="English note"></textarea></label>
        <button class="save-btn" :disabled="!tempEvent.title.trim() || savingEvent" @click="saveEvent">
          {{ savingEvent ? '保存中...' : '保存 Save' }}
        </button>
      </div>
    </template>

    <!-- ════ 编辑弹窗 ════ -->
    <div v-if="showEditForm" class="modal-overlay" @click.self="closeEditForm">
      <div class="modal-content">
        <h3>编辑 · Edit</h3>
        <div class="add-form">
          <label class="form-field"><span class="field-label">标题 Title</span><input v-model="tempEvent.title" class="form-input" /></label>
          <label class="form-field"><span class="field-label">英文 Title (EN)</span><input v-model="tempEvent.titleEn" class="form-input" /></label>
          <label class="form-field"><span class="field-label">日期 Date</span><input v-model="tempEvent.eventDate" type="date" class="form-input" /></label>
          <label class="form-field">
            <span class="field-label">类型 Type</span>
            <select v-model="tempEvent.eventType" class="form-select">
              <option value="personal">个人 Personal</option>
              <option value="todo">待办 Todo</option>
              <option value="anniversary">纪念日 Anniversary</option>
              <option value="birthday">生日 Birthday</option>
            </select>
          </label>
          <label class="form-field"><span class="field-label">备注 Note</span><textarea v-model="tempEvent.note" class="form-textarea"></textarea></label>
          <label class="form-field"><span class="field-label">英文 Note (EN)</span><textarea v-model="tempEvent.noteEn" class="form-textarea"></textarea></label>
          <div class="modal-btns">
            <button class="save-btn" :disabled="!tempEvent.title.trim() || savingEvent" @click="saveEvent">{{ savingEvent ? '保存中...' : '保存 Save' }}</button>
            <button class="cancel-btn" @click="closeEditForm">取消 Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ════ 删除确认 ════ -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal-content modal-small">
        <h3>确认删除 · Confirm Delete</h3>
        <p>确定要删除这个事件吗？</p>
        <p class="modal-sub">Are you sure you want to delete this event?</p>
        <div class="modal-btns">
          <button class="del-confirm-btn" @click="doDelete(deletingId!)">删除 Delete</button>
          <button class="cancel-btn" @click="showDeleteConfirm = false">取消 Cancel</button>
        </div>
      </div>
    </div>

    <!-- ════ 祝福弹窗 ════ -->
    <div v-if="showGreeting && grettingData" class="modal-overlay" @click.self="closeGreeting">
      <div class="modal-content modal-greeting">
        <h3>🎉 祝福 · Greeting</h3>
        <div class="greeting-box">
          <p class="greeting-text">{{ grettingData.zh }}</p>
          <p class="greeting-text-en">{{ grettingData.en }}</p>
        </div>
        <button class="save-btn" @click="closeGreeting">关闭 Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── 页面容器 ── */
.reminder-page {
  min-height: 100dvh;
  padding: 1rem;
  padding-bottom: 5rem;
  background: var(--bg, #0a0a1a);
  color: var(--text, #e0e0f0);
}

/* ── 加载 ── */
.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60dvh;
  gap: 1rem;
}
.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid rgba(167, 139, 250, 0.3);
  border-top-color: #a78bfa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 日历头部 ── */
.cal-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 0;
  position: relative;
}
.month-title {
  font-size: 1.15rem;
  font-weight: 600;
  min-width: 10rem;
  text-align: center;
  background: linear-gradient(135deg, #c084fc, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.nav-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: #aaa;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.nav-btn:hover { background: rgba(167,139,250,0.2); color: #a78bfa; }
.today-btn {
  position: absolute;
  right: 0;
  background: none;
  border: 1px solid rgba(167,139,250,0.3);
  color: #a78bfa;
  font-size: 0.7rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.4rem;
  cursor: pointer;
}
.today-btn:hover { background: rgba(167,139,250,0.15); }

/* ── 星期行 ── */
.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  padding: 0.3rem 0;
  color: var(--text-muted, #666);
  font-size: 0.75rem;
  font-weight: 500;
}

/* ── 日历网格 ── */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.cal-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: rgba(255,255,255,0.02);
  border: 1px solid transparent;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
  padding: 2px;
}
.cal-day.current-month { color: var(--text, #e0e0f0); }
.cal-day.other-month { color: var(--text-muted, #444); }
.cal-day.is-today { border-color: rgba(167,139,250,0.5); background: rgba(167,139,250,0.08); }
.cal-day.has-events { background: rgba(167,139,250,0.05); }
.cal-day:hover { background: rgba(167,139,250,0.12); }
.day-num { font-size: 0.85rem; font-weight: 500; line-height: 1; }
.day-dots { display: flex; gap: 2px; }
.day-dot { width: 4px; height: 4px; border-radius: 50%; }

/* ── 日视图 ── */
.day-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0;
}
.day-title { font-size: 1rem; font-weight: 600; color: #a78bfa; }
.back-btn, .add-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: #aaa;
  padding: 0.3rem 0.6rem;
  border-radius: 0.4rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}
.back-btn:hover, .add-btn:hover { background: rgba(167,139,250,0.2); color: #a78bfa; }

/* ── 事件列表 ── */
.event-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.5rem 0;
}
.event-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-left: 3px solid;
  border-radius: 0.6rem;
  padding: 0.75rem;
}
.event-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}
.event-type-badge {
  font-size: 0.6rem;
  padding: 0.15rem 0.4rem;
  border-radius: 0.3rem;
  color: #fff;
  font-weight: 500;
}
.event-actions { display: flex; gap: 0.3rem; }
.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0.15rem;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.action-btn:hover { opacity: 1; }
.action-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.event-title { font-size: 0.95rem; font-weight: 600; margin: 0; }
.event-title-en { font-size: 0.8rem; color: var(--text-muted, #888); margin: 0.1rem 0 0; font-style: italic; }
.event-note { font-size: 0.8rem; color: var(--text-secondary, #aaa); margin: 0.3rem 0 0; }
.event-note-en { font-size: 0.75rem; color: var(--text-muted, #888); margin: 0.1rem 0 0; font-style: italic; }
.culture-box {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(245,158,11,0.08);
  border-radius: 0.4rem;
  border-left: 2px solid #f59e0b;
}
.culture-text { font-size: 0.75rem; color: #fbbf24; margin: 0; }
.culture-text-en { font-size: 0.7rem; color: #d97706; margin: 0.2rem 0 0; font-style: italic; }

/* ── 空状态 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  text-align: center;
  color: var(--text-muted, #666);
}
.empty-icon { font-size: 2rem; }

/* ── 添加/编辑表单 ── */
.add-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
}
.add-title { font-size: 1rem; font-weight: 600; color: #a78bfa; }
.add-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.5rem 0;
}
.form-field { display: flex; flex-direction: column; gap: 0.25rem; }
.field-label { font-size: 0.75rem; color: var(--text-muted, #888); font-weight: 500; }
.form-input, .form-select, .form-textarea {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 0.4rem;
  padding: 0.5rem;
  color: #e0e0f0;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}
.form-input:focus, .form-select:focus, .form-textarea:focus { border-color: #a78bfa; }
.form-textarea { min-height: 3rem; resize: vertical; }
.form-select { cursor: pointer; }
.save-btn {
  background: linear-gradient(135deg, #a78bfa, #818cf8);
  border: none;
  color: #fff;
  padding: 0.6rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.save-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.save-btn:hover:not(:disabled) { opacity: 0.9; }
.cancel-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: #aaa;
  padding: 0.6rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
}
.cancel-btn:hover { background: rgba(255,255,255,0.1); }

/* ── 弹窗 ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 1rem;
}
.modal-content {
  background: #1a1a2e;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 0.8rem;
  padding: 1.25rem;
  width: 100%;
  max-width: 24rem;
  max-height: 80dvh;
  overflow-y: auto;
}
.modal-content h3 { margin: 0 0 0.75rem; font-size: 1rem; color: #a78bfa; }
.modal-small { max-width: 20rem; text-align: center; }
.modal-sub { font-size: 0.8rem; color: var(--text-muted, #888); }
.modal-btns { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
.del-confirm-btn {
  background: #ef4444;
  border: none;
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 0.4rem;
  font-size: 0.85rem;
  cursor: pointer;
}
.del-confirm-btn:hover { background: #dc2626; }

/* ── 祝福弹窗 ── */
.modal-greeting { max-width: 28rem; }
.greeting-box {
  background: rgba(245,158,11,0.06);
  border: 1px solid rgba(245,158,11,0.15);
  border-radius: 0.6rem;
  padding: 1rem;
  margin-bottom: 0.75rem;
}
.greeting-text {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #fbbf24;
  white-space: pre-wrap;
  margin: 0;
}
.greeting-text-en {
  font-size: 0.85rem;
  line-height: 1.5;
  color: #d97706;
  white-space: pre-wrap;
  margin: 0.5rem 0 0;
  font-style: italic;
}
</style>