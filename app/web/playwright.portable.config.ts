import { defineConfig } from '@playwright/test'
import pilot from './playwright.pilot.config'

// Reuse Playwright's cross-platform startup, readiness and owned-process teardown.
// Playwright resolves relative cwd from the config directory, including paths with spaces.
// These commands are fixed and run only the original test fixture from this archive.
export default defineConfig(pilot, {
  globalTimeout: 10 * 60_000,
  webServer: [
    {
      command: 'python -m uvicorn app_tests.synthetic_pilot_server:create_app --factory --host 127.0.0.1 --port 8000',
      cwd: '../..',
      url: 'http://127.0.0.1:8000/api/library',
      env: { PYTHONPATH: '', PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8' },
      reuseExistingServer: false,
      timeout: 60_000,
      stdout: 'ignore', stderr: 'ignore',
    },
    {
      command: 'node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 5173 --strictPort',
      cwd: '.',
      url: 'http://127.0.0.1:5173/',
      reuseExistingServer: false,
      timeout: 60_000,
      stdout: 'ignore', stderr: 'ignore',
    },
  ],
})
