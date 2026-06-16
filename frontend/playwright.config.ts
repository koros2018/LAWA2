import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: 'e2e-report' }]],
  use: {
    baseURL: 'http://localhost:6292',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'cd .. && python3 -m uvicorn main:app --host 0.0.0.0 --port 6290',
      url: 'http://localhost:6290/health',
      reuseExistingServer: true,
      timeout: 10000,
    },
    {
      command: 'npx vite preview --port 6292',
      url: 'http://localhost:6292',
      reuseExistingServer: true,
      timeout: 10000,
    },
  ],
})
