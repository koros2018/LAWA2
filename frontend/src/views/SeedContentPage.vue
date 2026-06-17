<template>
  <div class="seed-content-page">
    <!-- ════ 头部 ════ -->
    <header class="page-header">
      <div>
        <h1>内容管理 · Content Management</h1>
        <p class="subtitle">管理种子语料 · Manage seed content</p>
      </div>
      <button class="primary-btn" @click="openEdit()">
        ➕ 新建 · New
      </button>
    </header>

    <!-- ════ 筛选栏 ════ -->
    <div class="filter-bar">
      <div class="search-input">
        <span>🔍</span>
        <input v-model="search" placeholder="搜索 · Search..." />
      </div>
      <select v-model="selectedType">
        <option value="">全部类型 · All Types</option>
        <option v-for="t in CONTENT_TYPES" :key="t.value" :value="t.value">
          {{ t.label }}
        </option>
      </select>
    </div>

    <!-- ════ 内容列表 ════ -->
    <div v-if="loading" class="loading-state">
      <span>⏳</span>
      <p>加载中 · Loading...</p>
    </div>

    <div v-else-if="contents.length === 0" class="empty-state">
      <span>📦</span>
      <p>暂无数据 · Nothing yet</p>
      <p class="hint">点击「新建」添加第一个 · Tap "New" to add your first</p>
    </div>

    <div v-else class="content-list">
      <div v-for="item in contents" :key="item.id" class="content-card">
        <div class="card-header">
          <span class="type-badge">{{ typeLabels[item.content_type]?.label || item.content_type }}</span>
          <span v-if="item.is_system" class="system-badge">系统 · System</span>
          <span v-if="item.difficulty" class="difficulty-badge">
            {{ difficultyLabels[item.difficulty]?.label || item.difficulty }}
          </span>
          <span v-if="!item.is_active" class="inactive-badge">停用 · Inactive</span>
        </div>
        <h3 class="card-title">
          {{ item.title }}
          <span class="title-en">{{ item.title_en }}</span>
        </h3>
        <div class="card-tags" v-if="item.tags?.length">
          <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
        <div class="card-actions">
          <button class="action-btn" @click="openEdit(item)">✏️ 编辑 · Edit</button>
          <button v-if="!item.is_system" class="action-btn danger" @click="confirmDelete(item)">
            🗑️ 删除 · Delete
          </button>
        </div>
      </div>
    </div>

    <!-- ════ 分页 ════ -->
    <div v-if="total > pageSize" class="pagination">
      <button :disabled="page <= 1" @click="page--; loadContents()">◀️ 上一页 · Prev</button>
      <span>第 {{ page }} 页 / 共 {{ Math.ceil(total / pageSize) }} 页 · Page {{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button :disabled="page * pageSize >= total" @click="page++; loadContents()">下一页 · Next ▶️</button>
    </div>

    <!-- ════ 编辑模态框 ════ -->
    <div v-if="showModal && editingContent" class="modal-overlay" @click="closeEdit()">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>{{ editingContent.id ? '编辑 · Edit' : '新建 · New' }}</h2>
          <button class="close-btn" @click="closeEdit()">✕</button>
        </div>
        <form @submit.prevent="handleSubmit" class="modal-form">
          <div class="form-row">
            <div class="form-group">
              <label>类型 · Type</label>
              <select v-model="editingContent.content_type">
                <option v-for="t in CONTENT_TYPES" :key="t.value" :value="t.value">
                  {{ t.label }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>难度 · Difficulty</label>
              <select v-model="editingContent.difficulty">
                <option value="">无 · None</option>
                <option v-for="d in DIFFICULTIES" :key="d.value" :value="d.value">
                  {{ d.label }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>标题 · Title</label>
              <input v-model="editingContent.title" placeholder="中文标题 · Chinese title" required />
            </div>
            <div class="form-group">
              <label>标题 · Title</label>
              <input v-model="editingContent.title_en" placeholder="English title" required />
            </div>
          </div>
          <div class="form-group">
            <label>内容 · Content</label>
            <textarea v-model="editingContent.content" placeholder="中文内容 · Chinese content" rows="4"></textarea>
          </div>
          <div class="form-group">
            <label>内容 · Content</label>
            <textarea v-model="editingContent.content_en" placeholder="English content" rows="4"></textarea>
          </div>
          <div class="form-group">
            <label>标签 · Tags (逗号分隔 · Comma separated)</label>
            <input v-model="tagInput" placeholder="科技, 日常, 商务 · Tech, Daily, Business" />
          </div>
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="editingContent.is_active" />
              启用 · Active
            </label>
          </div>
          <div class="modal-actions">
            <button type="button" class="secondary-btn" @click="closeEdit()">取消 · Cancel</button>
            <button type="submit" class="primary-btn">保存 · Save</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSeedContent } from '@/api/seed'

const {
  contents,
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
} = useSeedContent()

const tagInput = ref('')

onMounted(() => {
  loadContents()
})

async function handleSubmit() {
  if (!editingContent.value) return
  editingContent.value.tags = tagInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t)
  await saveContent(editingContent.value)
  closeEdit()
}

async function confirmDelete(item: any) {
  if (confirm(`确定删除 "${item.title}"？\nConfirm delete "${item.title}"?`)) {
    await removeContent(item.id)
  }
}
</script>

<style scoped>
.seed-content-page {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 1.5rem;
  margin: 0;
  color: #2c3e50;
}

.subtitle {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin: 4px 0 0 0;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 8px 12px;
}

.search-input input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.9rem;
  outline: none;
}

.filter-bar select {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.9rem;
  background: white;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-card {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 16px;
}

.card-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.type-badge {
  background: #e3f2fd;
  color: #1565c0;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
}

.system-badge {
  background: #fff3e0;
  color: #e65100;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
}

.difficulty-badge {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
}

.inactive-badge {
  background: #ffebee;
  color: #c62828;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
}

.card-title {
  margin: 0 0 8px 0;
  font-size: 1.1rem;
}

.title-en {
  display: block;
  font-size: 0.8rem;
  color: #7f8c8d;
  font-weight: normal;
}

.card-tags {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.tag {
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #666;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.85rem;
}

.action-btn.danger {
  border-color: #ffcdd2;
  color: #c62828;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: #7f8c8d;
}

.loading-state span,
.empty-state span {
  font-size: 2rem;
  display: block;
  margin-bottom: 8px;
}

.hint {
  font-size: 0.85rem;
  margin-top: 8px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding: 16px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  font-size: 0.85rem;
  color: #7f8c8d;
}

/* ── Modal ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #7f8c8d;
}

.modal-form {
  padding: 20px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.85rem;
  color: #555;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.9rem;
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-group.checkbox {
  flex-direction: row;
  align-items: center;
}

.form-group.checkbox label {
  font-weight: normal;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.primary-btn {
  padding: 10px 24px;
  background: #1565c0;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
}

.secondary-btn {
  padding: 10px 24px;
  background: #f5f5f5;
  color: #555;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
}
</style>
