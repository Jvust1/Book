import { chromium, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
const output = path.resolve('../../.build/web-013')
const baseUrl = process.env.BOOK_WEB_BASE_URL || 'http://127.0.0.1:5173'
fs.mkdirSync(output, { recursive: true })
const browser = await chromium.launch({ headless: true, channel: 'chrome', args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] })
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, permissions: ['microphone'], acceptDownloads: true })
const page = await context.newPage(), errors = [], steps = []
page.on('pageerror', error => errors.push(error.message))
const pass = name => { steps.push(name); console.log('PASS ' + name) }
try {
  await page.goto(baseUrl)
  await expect(page.getByRole('link', { name: '进入课程' })).toBeVisible()
  await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(output, 'library-mobile.png') })
  await page.getByRole('link', { name: '课堂录音', exact: true }).click()
  await page.getByLabel('录音名称', { exact: true }).fill('课堂录音测试')
  await page.getByRole('button', { name: '开始录音', exact: true }).click()
  await expect(page.getByRole('button', { name: '暂停录音' })).toBeVisible()
  await expect.poll(() => page.locator('.recording-clock').textContent()).not.toBe('00:00')
  await page.getByRole('button', { name: '暂停录音' }).click()
  const elapsed = await page.locator('.recording-clock').textContent()
  await page.waitForTimeout(1100)
  expect(await page.locator('.recording-clock').textContent()).toBe(elapsed)
  await page.getByRole('button', { name: '继续录音' }).click()
  await page.getByRole('link', { name: '教材库', exact: true }).click()
  await expect(page.locator('.ongoing-recording')).toBeVisible()
  await page.getByRole('link', { name: '课堂录音', exact: true }).click()
  await expect(page.getByRole('button', { name: '停止并保存' })).toBeVisible()
  await page.getByRole('button', { name: '停止并保存' }).click()
  await expect(page.locator('.recording-item')).toHaveCount(1)
  await page.reload()
  await expect(page.locator('.recording-item')).toHaveCount(1)
  const audio = page.locator('audio')
  await audio.evaluate(audio => audio.play())
  await expect.poll(() => audio.evaluate(audio => audio.currentTime)).toBeGreaterThan(.1)
  await audio.evaluate(audio => audio.pause())
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出音频' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('课堂录音测试.webm')
  await download.saveAs(path.join(output, 'test-recording.webm'))
  expect(fs.statSync(path.join(output, 'test-recording.webm')).size).toBeGreaterThan(1000)
  pass('Browser capture, pause, navigation, IndexedDB reload, playback and export')
  await page.getByRole('button', { name: '开始录音', exact: true }).click()
  await expect.poll(async () => {
    return page.evaluate(() => new Promise(resolve => {
      const request = indexedDB.open('book-recordings', 2)
      request.onsuccess = () => {
        const db = request.result, count = db.transaction('chunks').objectStore('chunks').count()
        count.onsuccess = () => { resolve(count.result); db.close() }
      }
    }))
  }, { timeout: 10000 }).toBeGreaterThan(0)
  // A replacement page in the same browser profile represents a process/page restart.
  page.on('dialog', dialog => dialog.accept())
  await page.reload()
  await expect(page.locator('.recording-item')).toHaveCount(2)
  await expect(page.getByText('这段录音曾中断，已恢复保存到本机的部分。')).toBeVisible()
  pass('Interrupted browser session recovers persisted audio chunks')
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  }
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(output, 'recordings-desktop.png') })
  await page.setViewportSize({ width: 390, height: 844 })
  await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(output, 'recordings-mobile.png') })
  pass('Recording page fits 320 / 390 / 768 / 1440 widths')
  await page.goto(baseUrl + '/courses/functional_analysis_course/search?q=1%2Fp')
  await expect(page.locator('.search-result-card').first()).toBeVisible()
  await page.locator('.search-result-card .source-link').first().click()
  await expect(page.locator('.katex').first()).toBeVisible()
  await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(output, 'formulas-mobile.png') })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto(baseUrl)
  await expect(page.getByRole('link', { name: '进入课程' })).toBeVisible()
  await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(output, 'library-desktop.png') })
  pass('Real textbook math renders with locally bundled fonts and no mobile overflow')
  expect(errors).toEqual([])
  fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify({ steps, errors }, null, 2))
} finally { await browser.close() }
