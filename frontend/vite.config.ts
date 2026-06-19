import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 6291,
    proxy: {
      '/api': {
        target: 'http://localhost:6290',
        changeOrigin: true,
      },
      '/agent': {
        target: 'http://localhost:6290',
        changeOrigin: true,
      },
    },
    // 防止 SPA fallback 拦截 manifest.json
    fs: {
      strict: false,
    },
    origin: 'http://localhost:6291',
  },
  appType: 'spa',
})
