// LAWA2 Service Worker - v4.5.1
// 离线缓存策略：App Shell + 静态资源

const CACHE_NAME = 'lawa2-v4.5.1'
const OFFLINE_PAGE = '/offline.html'

// 核心资源缓存列表
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/offline.html',
]

// 安装：缓存静态资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS)
    })
  )
  self.skipWaiting()
})

// 激活：清理旧缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    })
  )
  self.clients.claim()
  // 通知所有客户端强制刷新
  self.clients.matchAll().then(clients => {
    clients.forEach(client => client.postMessage({ type: 'CACHE_UPDATED' }))
  })
})

// 网络请求策略：Stale-While-Revalidate（静态资源）+ Network-First（API）
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // manifest.json：始终从网络获取（Network-First），防止缓存污染
  if (url.pathname.endsWith('/manifest.json')) {
    event.respondWith(networkFirst(request))
    return
  }

  // API 请求：Network-First
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request))
    return
  }

  // 静态资源：Stale-While-Revalidate
  if (request.destination === 'script' ||
      request.destination === 'style' ||
      request.destination === 'image' ||
      request.destination === 'font') {
    event.respondWith(staleWhileRevalidate(request))
    return
  }

  // 导航请求：Network-First，失败回退到 App Shell
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, '/'))
    return
  }
})

// Network-First 策略
async function networkFirst(request, fallback = null) {
  try {
    const response = await fetch(request)
    // 成功则缓存更新
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, response.clone())
    }
    return response
  } catch (error) {
    // 网络失败，尝试从缓存读取
    const cached = await caches.match(request)
    if (cached) return cached
    // 导航请求回退到首页
    if (fallback && request.mode === 'navigate') {
      return caches.match(fallback)
    }
    // 其他情况返回离线页面
    if (request.mode === 'navigate') {
      return caches.match(OFFLINE_PAGE)
    }
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' })
  }
}

// Stale-While-Revalidate 策略
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME)
  const cached = await cache.match(request)

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone())
    }
    return response
  }).catch(() => null)

  return cached || fetchPromise || new Response('Offline', { status: 503 })
}

// 后台消息处理
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})
