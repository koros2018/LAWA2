/**
 * LAWA2 — 全局错误处理工具
 * 统一错误捕获、用户提示、重试机制
 */

import { ref, type Ref } from 'vue'

export interface ToastMessage {
  type: 'error' | 'success' | 'warning' | 'info'
  message: string
  messageEn: string
}

export const toast = ref<ToastMessage | null>(null)

export function showToast(
  type: ToastMessage['type'],
  message: string,
  messageEn?: string
) {
  toast.value = { type, message, messageEn: messageEn || message }
  setTimeout(() => { toast.value = null }, 4000)
}

export function handleApiError(
  e: unknown,
  fallbackMsg: string = '操作失败 · Operation failed',
  fallbackMsgEn: string = 'Operation failed',
  toastRef: Ref<ToastMessage | null> = toast
): string {
  let msg = fallbackMsg
  let msgEn = fallbackMsgEn

  if (e instanceof Error) {
    msg = e.message
    msgEn = e.message
  } else if (typeof e === 'object' && e !== null && 'message' in e) {
    msg = String((e as { message: unknown }).message)
    msgEn = msg
  } else if (typeof e === 'string') {
    msg = e
    msgEn = e
  }

  // 解析 API 错误
  if (typeof e === 'object' && e !== null && 'detail' in e) {
    const detail = (e as { detail: unknown }).detail
    if (Array.isArray(detail)) {
      msg = detail.map(d => d.msg || d.message || String(d)).join(' · ')
      msgEn = msg
    } else if (typeof detail === 'string') {
      msg = detail
      msgEn = detail
    }
  }

  // HTTP 状态码友好提示
  if (typeof e === 'object' && e !== null && 'status' in e) {
    const status = (e as { status: number }).status
    switch (status) {
      case 401: msg = '未授权 · Not authorized'; msgEn = 'Not authorized'; break
      case 403: msg = '无权限 · No permission'; msgEn = 'No permission'; break
      case 404: msg = '资源不存在 · Not found'; msgEn = 'Not found'; break
      case 405: msg = '方法不支持 · Method not allowed'; msgEn = 'Method not allowed'; break
      case 422: msg = '参数错误 · Invalid parameters'; msgEn = 'Invalid parameters'; break
      case 500: msg = '服务器错误 · Server error'; msgEn = 'Server error'; break
      case 503: msg = '服务不可用 · Service unavailable'; msgEn = 'Service unavailable'; break
    }
  }

  // 网络错误
  if (typeof e === 'object' && e !== null && 'name' in e && (e as { name: string }).name === 'TypeError') {
    msg = '网络错误 · Network error · 请检查连接'
    msgEn = 'Network error · Please check your connection'
  }

  // 显示 toast
  showToast('error', msg, msgEn)
  console.error(`[LAWA2 Error] ${msg}:`, e)

  return msg
}

/** 带重试机制的 API 调用 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 2,
  delayMs: number = 500
): Promise<T> {
  let lastError: unknown
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn()
    } catch (e) {
      lastError = e
      if (i < maxRetries) {
        await new Promise(r => setTimeout(r, delayMs * (i + 1)))
      }
    }
  }
  throw lastError
}
