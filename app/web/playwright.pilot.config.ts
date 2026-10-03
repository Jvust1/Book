import { defineConfig } from '@playwright/test'
import base from './playwright.config'

export default defineConfig(base, {
  testDir: './pilot',
  // These real API journeys share one temporary SQLite profile.
  workers: 1,
  timeout: 60_000,
  outputDir: './pilot-test-results',
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'pilot-playwright-report' }]],
})
