<script setup lang="ts">
</script>

<template>
  <div class="agent-page admin-page">
    <div class="agent-header">
      <span class="agent-icon">⚙️</span>
      <h1>管理 · Admin</h1>
    </div>
    <p class="coming-soon">Coming soon · 即将上线</p>
    <p class="sub-text">用户管理、内容管理、数据看板</p>
    <p class="sub-text-en">User management, content management, and data dashboard</p>
  </div>
</template>

<style scoped>
.agent-page {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}
.agent-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.agent-icon {
  font-size: 2rem;
}
h1 {
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(135deg, #c084fc, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.coming-soon {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}
.sub-text {
  color: var(--text-muted);
  font-size: 0.9rem;
}
.sub-text-en {
  color: var(--text-muted);
  font-size: 0.85rem;
  font-style: italic;
  margin-top: 0.25rem;
}
</style>