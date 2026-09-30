import { expect, test } from '@playwright/test'

const course = 'original_algebra_pilot'
const section = 'original_s01'
const qaPath = `/courses/${course}/qa?section=${section}`
const notice = '浏览器会话存储不可用，当前仅在页面内存临时保留近期返回位置和问答；刷新或关闭后会丢失。'

// Uses the same real file-backed API/runtime as chapter-pilot.spec.ts. No HTTP mocks.
for (const failure of ['blocked-access', 'quota-full'] as const) {
  test(`QA and source round trip survive ${failure} with explicit memory-only retention`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.addInitScript(mode => {
      if (mode === 'blocked-access') {
        Object.defineProperty(window, 'sessionStorage', { configurable: true,
          get() { throw new DOMException('Test: storage denied', 'SecurityError') } })
      } else {
        const original = Storage.prototype.setItem
        Storage.prototype.setItem = function (key, value) {
          if (this === window.sessionStorage) throw new DOMException('Test: storage full', 'QuotaExceededError')
          return original.call(this, key, value)
        }
      }
    }, failure)
    const errors: string[] = []
    let asks = 0
    page.on('pageerror', error => errors.push(error.message))
    page.on('request', request => {
      if (request.method() === 'POST' && request.url().endsWith(`/api/courses/${course}/qa`)) asks++
    })
    await page.goto(qaPath)
    await expect(page.getByRole('heading', { name: '教材问答', exact: true })).toBeVisible()
    if (failure === 'blocked-access') await expect(page.getByText(notice, { exact: true })).toBeVisible()
    await page.getByRole('textbox', { name: '教材问题' }).fill('倍增规则')
    await page.getByRole('button', { name: '提问', exact: true }).click()
    await expect(page.locator('.qa-answer-card')).toHaveCount(1)
    await expect(page.getByText(notice, { exact: true })).toBeVisible()
    await page.getByText('查看回答原文', { exact: true }).click()
    const originalAnswer = await page.locator('.qa-original-answer pre').innerText()
    await page.locator('.qa-citation-card').getByRole('link', { name: '查看教材来源' }).click()
    await expect(page.getByText('结构化来源：object:doubling_rule', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '返回问答', exact: true }).click()
    await expect(page.locator('.qa-answer-card')).toHaveCount(1)
    await page.getByText('查看回答原文', { exact: true }).click()
    await expect(page.locator('.qa-original-answer pre')).toHaveText(originalAnswer)
    expect(asks).toBe(1)
    await expect(page.locator('.qa-citation-card[aria-current="true"]')).toHaveCount(1)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: `pilot-test-results/session-storage-${failure}-narrow.png`, fullPage: true })
    // Memory-only is not disguised as durable persistence.
    await page.reload()
    await expect(page.getByRole('heading', { name: '教材问答', exact: true })).toBeVisible()
    await expect(page.locator('.qa-answer-card, .qa-question-card')).toHaveCount(0)
    expect(asks).toBe(1)
    expect(errors).toEqual([])
  })
}
