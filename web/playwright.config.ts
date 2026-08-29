import { defineConfig, devices } from '@playwright/test';

const WEB = 'http://127.0.0.1:4311';
const API = 'http://127.0.0.1:8111';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: process.env['CI'] ? 1 : 0,
  reporter: process.env['CI'] ? [['github'], ['list']] : [['list']],
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: WEB,
    trace: 'retain-on-failure',
    locale: 'pt-BR',
    timezoneId: 'America/Sao_Paulo',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: 'python -m uvicorn app.main:app --host 127.0.0.1 --port 8111 --log-level warning',
      cwd: '../backend',
      url: `${API}/api/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        APP_ENV: 'development',
        DATABASE_URL: 'sqlite:///./.cache/e2e.db',
        CACHE_DB_PATH: './.cache/e2e_cache.db',
        ALLOWED_ORIGINS: WEB,
      },
    },
    {
      command: 'npx ng build --configuration e2e && node dist/fiance/server/server.mjs',
      url: WEB,
      reuseExistingServer: false,
      timeout: 300_000,
      env: {
        PORT: '4311',
        ALLOWED_HOSTS: '127.0.0.1,localhost',
      },
    },
  ],
});
