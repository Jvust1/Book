import react from '@vitejs/plugin-react'
import { configDefaults, defineConfig } from 'vitest/config'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    VitePWA({
      // Android already ships its assets; a service worker can serve stale UI
      // after an APK upgrade instead of the newly bundled version.
      disable: mode === 'android',
      registerType: 'autoUpdate',
      manifest: {
        name: 'Book 学习',
        short_name: 'Book',
        description: '中文优先的本地教材学习应用',
        display: 'standalone',
        start_url: '/',
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2,ttf}'],
        navigateFallback: '/index.html',
        runtimeCaching: [],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    clearMocks: true,
    exclude: [...configDefaults.exclude, 'e2e/**'],
  },
}))
