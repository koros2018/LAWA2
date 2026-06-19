import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')

// ── PWA Service Worker 注册 ──
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      })
      console.log('[SW] Registered:', registration.scope)

      // 监听消息（SW 通知缓存更新）
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data?.type === 'CACHE_UPDATED') {
          console.log('[SW] Cache updated, refreshing...')
          window.location.reload()
        }
      })

      // 监听更新
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // 有新版本可用，提示用户刷新
              console.log('[SW] New version available. Refresh to update.')
            }
          })
        }
      })
    } catch (error) {
      console.error('[SW] Registration failed:', error)
    }
  })
}