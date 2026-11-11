import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir: './tests', testMatch: '**/*.spec.ts', workers: 1, timeout: 90000,
  use: { baseURL: 'http://localhost:8081', headless: true, launchOptions: { executablePath: '/usr/bin/chromium', args: ['--no-sandbox'] } },
  webServer: { command: 'npm run web -- --port 8081', url: 'http://localhost:8081', reuseExistingServer: true, timeout: 60000 }
});
