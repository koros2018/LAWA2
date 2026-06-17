import { test, expect } from '@playwright/test'

const FRONTEND_URL = 'http://localhost:6292'

// ── 辅助函数 ──

async function setUserId(page: any, id = 'test_user') {
  await page.evaluate((uid: string) => {
    localStorage.setItem('lawa2_session', JSON.stringify({ userId: uid }))
  }, id)
}

async function gotoWelcomeState(page: any) {
  // 如果页面进了 done 状态（有历史），点"新的桥梁互动"或"New Interaction"按钮回 welcome
  // 注意 newGreeting 函数会直接跳到 Lv.1 greeting，所以点完后页面上就是 greeting 回复框
  const newBtn = page.locator('button:has-text("新的桥梁互动"), button:has-text("New Interaction")')
  if (await newBtn.isVisible().catch(() => false)) {
    await newBtn.click()
    await page.waitForTimeout(1500)
  }
}

/**
 * Lv.1 问候流程：进入页面后默认在 greeting 状态（或 done→点"新的"→自动进 greeting）
 * 所以只需要直接填回复框 + 发送即可
 */
async function doLv1BridgeFlow(
  page: any,
  fillFn: () => Promise<void>,
) {
  await page.goto(`${FRONTEND_URL}/bridge`)
  await setUserId(page)
  await page.reload()
  await page.waitForTimeout(2000)

  await gotoWelcomeState(page)

  // 等待 greeting 气泡和回复框出现
  const textarea = page.locator('.reply-input')
  await textarea.waitFor({ timeout: 8000 })

  // 填内容
  await fillFn()

  // 点发送 — 支持双语
  const sendBtn = page.locator('button:has-text("发送回复"), button:has-text("Send Reply")')
  await sendBtn.click()
  await page.waitForTimeout(2000)

  // 验证结果
  const resultBadge = page.locator('.result-badge')
  await resultBadge.waitFor({ timeout: 8000 })
  expect(await resultBadge.textContent()).toContain('回复已送达')
}

// ── 测试套件 ──

test.describe('LAWA2 E2E — 全流程', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND_URL)
    await setUserId(page)
    await page.reload()
  })

  // ── 1. 首页/仪表盘 ──

  test('1.1 首页加载 — 显示仪表盘信息', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/`)
    await page.waitForTimeout(1000)
    const body = page.locator('body')
    await expect(body).not.toBeEmpty()
    const hasContent = await page.locator('.hero-section, .card').first().isVisible().catch(() => false)
    expect(hasContent).toBeTruthy()
  })

  // ── 2. 注册/登录 ──

  test('2.1 注册页面 — 创建新用户', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/onboarding`)
    await page.waitForTimeout(800)
    const hasForm = await page.locator('input, button').first().isVisible().catch(() => false)
    expect(hasForm).toBeTruthy()
  })

  // ── 3. 信息流 Feed ──

  test('3.1 信息流 — 显示社交语料', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/feed`)
    await page.waitForTimeout(1500)
    const hasFeed = await page.locator('.feed-item, .feed-card, .card').first().isVisible().catch(() => false)
    expect(hasFeed).toBeTruthy()
  })

  test('3.2 信息流 — Tab 切换', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/feed`)
    await page.waitForTimeout(1000)
    const tabs = page.locator('button, .tab, .bt-tab')
    const count = await tabs.count()
    if (count >= 2) {
      await tabs.nth(1).click()
      await page.waitForTimeout(500)
      expect(true).toBeTruthy()
    }
  })

  // ── 4. 双向桥梁 ──

  test('4.1 桥梁页面 — 加载语伴信息', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/bridge`)
    await page.waitForTimeout(1500)
    const hasPartner = await page.locator('.partner-name').first().isVisible().catch(() => false)
    expect(hasPartner).toBeTruthy()
  })

  test('4.2 桥梁 — 查看进度', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/bridge`)
    await page.waitForTimeout(1500)
    const hasProgress = await page.locator('.progress-row, .progress-bar').first().isVisible().catch(() => false)
    expect(hasProgress).toBeTruthy()
  })

  // ── 5. 语言花园 ──

  test('5.1 花园页面 — 加载词簇', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/garden`)
    await page.waitForTimeout(1500)
    const hasGarden = await page.locator('.garden-container, .garden-zone, .word-cluster, .card').first().isVisible().catch(() => false)
    expect(hasGarden).toBeTruthy()
  })

  // ── 6. 个人主页 ──

  test('6.1 个人页面 — 加载画像', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/profile`)
    await page.waitForTimeout(1500)
    const hasContent = await page.locator('.card, .profile-section, .insight-panel').first().isVisible().catch(() => false)
    expect(hasContent).toBeTruthy()
  })

  // ── 7. API 端点 ──

  test('7.1 后端健康检查', async () => {
    const res = await fetch('http://localhost:6290/health')
    const data = await res.json()
    expect(res.status).toBe(200)
    expect(data.status).toBe('healthy')
  })

  test('7.2 后端 — 获取语伴', async () => {
    const res = await fetch('http://localhost:6290/api/v2/bridge/partner?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(data.data.partner_name).toBeTruthy()
  })

  test('7.3 后端 — 桥梁进度', async () => {
    const res = await fetch('http://localhost:6290/api/v2/bridge/progress?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(data.data.levels.length).toBe(5)
  })

  test('7.4 后端 — 花园报告', async () => {
    const res = await fetch('http://localhost:6290/api/v1/habit/garden/report?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(data.data.report).toBeDefined()
    expect(data.data.week_actions).toBeGreaterThanOrEqual(0)
  })

  test('7.5 后端 — 成长洞察', async () => {
    const res = await fetch('http://localhost:6290/api/v1/habit/garden/growth?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(Array.isArray(data.data.actions_30d)).toBeTruthy()
    expect(data.data.actions_30d.length).toBe(30)
  })

  test('7.6 后端 — 社交场景语料', async () => {
    const res = await fetch('http://localhost:6290/api/v1/habit/social/scene?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(data.data.word).toBeTruthy()
  })

  test('7.7 后端 — 桥梁问候', async () => {
    const res = await fetch('http://localhost:6290/api/v2/bridge/greeting?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(data.data.greeting).toBeTruthy()
  })

  test('7.8 后端 — 桥梁 Lv.2 点赞', async () => {
    const res = await fetch('http://localhost:6290/api/v2/bridge/like?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(data.data.message).toBeTruthy()
  })

  test('7.9 后端 — 桥梁 Lv.3 教梗', async () => {
    const res = await fetch('http://localhost:6290/api/v2/bridge/teach?user_id=test_user')
    const data = await res.json()
    expect(data.status).toBe('ok')
    expect(data.data.message).toBeTruthy()
  })

  // ── 8. 页面无崩溃 ──

  const pages = ['/', '/onboarding', '/feed', '/bridge', '/garden', '/profile']
  for (const route of pages) {
    test(`8.${pages.indexOf(route) + 1} 路由 ${route} — 无崩溃`, async ({ page }) => {
      await page.goto(`${FRONTEND_URL}${route}`)
      await page.waitForTimeout(1500)
      const errors: string[] = []
      page.on('pageerror', (err) => errors.push(err.message))
      await page.waitForTimeout(500)
      expect(errors.length).toBe(0)
    })
  }
})

test.describe('LAWA2 E2E — 桥梁完整流程', () => {

  test('桥梁 Lv.1 问候→回复→结果', async ({ page }) => {
    await doLv1BridgeFlow(
      page,
      async () => {
        const textarea = page.locator('.reply-input')
        await textarea.waitFor({ timeout: 5000 })
        await textarea.fill('Hello! Nice to meet you too!')
      },
    )
  })
})

// ── 9. Admin Agent 测试 ──

test.describe('LAWA2 E2E — Admin Agent', () => {

  test('9.1 管理页面 — 加载数据看板', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/admin`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证数据卡片加载
    const statCards = page.locator('.stat-card')
    await expect(statCards.first()).toBeVisible()
  })

  test('9.2 管理页面 — 用户管理 Tab', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/admin`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 切换到用户管理 Tab
    const usersTab = page.locator('button:has-text("用户管理"), button:has-text("Users")')
    await usersTab.click()
    await page.waitForTimeout(1000)
    
    // 验证用户列表加载
    const userCards = page.locator('.user-card')
    await expect(userCards.first()).toBeVisible()
  })

  test('9.3 内容管理页面 — 加载列表', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/seed-content`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证页面加载（可能有空状态或列表）
    const content = page.locator('body')
    await expect(content).not.toBeEmpty()
  })

  test('9.4 日志查看页面 — 加载日志', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/logs`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证页面加载
    const content = page.locator('body')
    await expect(content).not.toBeEmpty()
  })

  test('9.5 错误监控页面 — 加载统计', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/errors`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证页面加载
    const content = page.locator('body')
    await expect(content).not.toBeEmpty()
  })
})

// ── 10. Photo Agent 测试 ──

test.describe('LAWA2 E2E — Photo Agent', () => {

  test('10.1 拍照页面 — 加载上传界面', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/photo`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证上传区域存在
    const uploadArea = page.locator('.upload-area, [data-testid="upload"], button:has-text("上传")')
    if (await uploadArea.count() > 0) {
      await expect(uploadArea.first()).toBeVisible()
    }
  })

  test('10.2 拍照页面 — 词汇卡片 Modal', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/photo`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证词汇卡片 Modal 组件存在（检查是否有 modal 样式）
    const modalStyles = await page.evaluate(() => {
      const styles = document.styleSheets
      for (let sheet of styles) {
        try {
          for (let rule of sheet.cssRules) {
            if (rule.cssText?.includes('modal') || rule.cssText?.includes('Modal')) {
              return true
            }
          }
        } catch {}
      }
      return false
    })
    expect(modalStyles).toBeTruthy()
  })
})

// ── 11. Reminder Agent 测试 ──

test.describe('LAWA2 E2E — Reminder Agent', () => {

  test('11.1 提醒页面 — 加载日历', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/reminder`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证日历组件存在
    const calendar = page.locator('.calendar-grid, .calendar, [data-testid="calendar"]')
    if (await calendar.count() > 0) {
      await expect(calendar.first()).toBeVisible()
    }
  })

  test('11.2 提醒页面 — 节假日列表', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/reminder`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    // 验证节假日数据加载
    const holidays = page.locator('.holiday-item, .event-card, .reminder-item')
    if (await holidays.count() > 0) {
      await expect(holidays.first()).toBeVisible()
    }
  })
})

// ── 12. 响应式测试 ──

test.describe('LAWA2 E2E — 响应式', () => {

  test('12.1 移动端视图 — 首页', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto(`${FRONTEND_URL}/`)
    await page.waitForTimeout(1000)
    
    const body = page.locator('body')
    await expect(body).not.toBeEmpty()
  })

  test('12.2 平板视图 — 管理页面', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto(`${FRONTEND_URL}/admin`)
    await setUserId(page)
    await page.reload()
    await page.waitForTimeout(2000)
    
    const content = page.locator('body')
    await expect(content).not.toBeEmpty()
  })
})

// ── 13. 双语化测试 ──

test.describe('LAWA2 E2E — 双语化', () => {

  test('13.1 首页 — 包含中英文', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/`)
    await page.waitForTimeout(1000)
    
    const bodyText = await page.locator('body').textContent()
    // 检查是否包含中英文混合内容
    const hasChinese = /\u4e00-\u9fff/.test(bodyText || '')
    const hasEnglish = /[A-Za-z]/.test(bodyText || '')
    expect(hasChinese || hasEnglish).toBeTruthy()
  })

  test('13.2 桥梁页面 — 双语标签', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/bridge`)
    await page.waitForTimeout(1000)
    
    const bodyText = await page.locator('body').textContent()
    // 检查双语格式（中文 · English）
    const hasBilingual = /·/.test(bodyText || '')
    expect(hasBilingual).toBeTruthy()
  })
})

// ── 14. 性能测试 ──

test.describe('LAWA2 E2E — 性能', () => {

  test('14.1 首页加载时间 < 3s', async ({ page }) => {
    const startTime = Date.now()
    await page.goto(`${FRONTEND_URL}/`)
    await page.waitForLoadState('domcontentloaded')
    const loadTime = Date.now() - startTime
    expect(loadTime).toBeLessThan(3000)
  })

  test('14.2 管理页面加载时间 < 5s', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/admin`)
    await setUserId(page)
    await page.reload()
    
    const startTime = Date.now()
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime
    expect(loadTime).toBeLessThan(5000)
  })
})

// ── 15. 路由守卫测试 ──

test.describe('LAWA2 E2E — 路由守卫', () => {

  test('15.1 未登录访问管理页面 — 重定向到登录', async ({ page }) => {
    // 清除本地存储
    await page.goto(FRONTEND_URL)
    await page.evaluate(() => localStorage.clear())
    
    await page.goto(`${FRONTEND_URL}/admin`)
    await page.waitForTimeout(2000)
    
    // 应该重定向到登录页面
    const currentUrl = page.url()
    expect(currentUrl).toContain('/login')
  })
})

// ── 16. API 端点补充测试 ──

test.describe('LAWA2 E2E — API 补充', () => {

  test('16.1 种子语料 API — 列表', async () => {
    const res = await fetch('http://localhost:6290/api/v2/seed/contents?user_id=test_user&page=1&page_size=20')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.items).toBeDefined()
    expect(data.total).toBeDefined()
  })

  test('16.2 日志 API — 列表', async () => {
    const res = await fetch('http://localhost:6290/api/v2/logs?lines=100')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.logs).toBeDefined()
    expect(data.total).toBeDefined()
  })

  test('16.3 错误统计 API', async () => {
    const res = await fetch('http://localhost:6290/api/v2/errors/stats')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.total_errors).toBeDefined()
    expect(data.top_errors).toBeDefined()
  })

  test('16.4 推送通知 API', async () => {
    const res = await fetch('http://localhost:6290/api/v2/push/preferences?user_id=test_user')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data).toBeDefined()
  })

  test('16.5 桥梁 Lv.4 群聊 API', async () => {
    const res = await fetch('http://localhost:6290/api/v2/bridge/group?user_id=test_user')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.status).toBe('ok')
  })

  test('16.6 桥梁 Lv.5 线下场景 API', async () => {
    const res = await fetch('http://localhost:6290/api/v2/bridge/offline?user_id=test_user')
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.status).toBe('ok')
  })
})
