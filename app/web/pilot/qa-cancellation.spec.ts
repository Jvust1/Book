import { expect, test } from '@playwright/test'
import type { Request } from '@playwright/test'

const course = 'original_algebra_pilot'
const section = 'original_s01'
const path = `/api/courses/${course}/qa`

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`stopping original QA waiting permits one explicit next question (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize(viewport)
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    let requests = 0
    let release!: () => void
    let fetched!: () => void
    let settled!: () => void
    let releaseSecond!: () => void
    let secondRequest: Request | null = null
    const releaseFirst = new Promise<void>(resolve => { release = resolve })
    const firstFetched = new Promise<void>(resolve => { fetched = resolve })
    const firstSettled = new Promise<void>(resolve => { settled = resolve })
    const secondGate = new Promise<void>(resolve => { releaseSecond = resolve })
    await page.route(`**${path}`, async route => {
      requests++
      if (requests === 2) {
        secondRequest = route.request()
        const response = await route.fetch()
        expect(response.ok()).toBe(true)
        await secondGate
        await route.fulfill({ response })
        return
      }
      if (requests !== 1) { await route.continue(); return }
      // Real original-fixture retrieval/generation finishes before the client stops.
      // Holding only delivery proves the UI must not claim server work was undone.
      const response = await route.fetch()
      expect(response.ok()).toBe(true)
      const body = await response.json()
      expect(body.answer_kind).toBe('generated')
      expect(body.citations[0]).toMatchObject({ source_id: 'doubling_rule', section_id: section })
      fetched()
      await releaseFirst
      try { await route.fulfill({ response }) } finally { settled() }
    })
    try {
      await page.goto(`/courses/${course}/qa?section=${section}`)
      await expect(page.getByText('当前范围：1.1 · 原创倍增小节', { exact: true })).toBeVisible()
      const input = page.getByRole('textbox', { name: '教材问题', exact: true })
      await input.fill('倍增规则')
      await page.getByRole('button', { name: '提问', exact: true }).click()
      await firstFetched
      await expect(page.getByRole('button', { name: '正在查找教材依据…', exact: true })).toBeDisabled()
      await page.getByRole('button', { name: '停止等待', exact: true }).click()
      const notice = page.getByRole('status')
      await expect(notice).toContainText('停止等待不代表远端已取消，也不会撤销服务器工作')
      await expect(notice).toContainText('不会自动重发')
      await expect(page.getByRole('button', { name: '提问', exact: true })).toBeEnabled()
      await expect(page.locator('.qa-answer-card')).toHaveCount(0)
      expect(requests).toBe(1)
      await page.screenshot({ path: `pilot-test-results/qa-stopped-${viewport.name}.png`, fullPage: true })
      await input.fill('倍增规则')
      await page.getByRole('button', { name: '提问', exact: true }).click()
      await expect.poll(() => requests).toBe(2) // The replacement POST was actually admitted.
      // Hold the second delivery while releasing the abandoned first response:
      // old completion must neither append an answer nor clear the newer wait.
      release()
      await firstSettled
      await expect(page.locator('.qa-answer-card')).toHaveCount(0)
      await expect(page.getByRole('button', { name: '正在查找教材依据…', exact: true })).toBeDisabled()
      const nextResponse = page.waitForResponse(response => response.request() === secondRequest)
      releaseSecond()
      expect((await (await nextResponse).json()).answer_kind).toBe('generated')
      await expect(page.locator('.qa-answer-card')).toHaveCount(1)
      expect(requests).toBe(2)
      const saved = await page.evaluate(courseId => JSON.parse(sessionStorage.getItem(`book:qa-session:${courseId}`)!), course)
      expect(saved.messages.map((message: { role: string }) => message.role)).toEqual(['user', 'user', 'assistant'])
      expect(new Set(saved.messages.map((message: { id: string }) => message.id)).size).toBe(3)
      await expect(page.getByText('回答依据：提问时的小节', { exact: true })).toBeVisible()
      await page.getByRole('link', { name: '查看教材来源', exact: true }).click()
      await expect(page.getByLabel('教材来源定位', { exact: true }).getByText('结构化来源：object:doubling_rule', { exact: true })).toBeVisible()
      await page.getByRole('button', { name: '返回问答', exact: true }).click()
      await expect(page.locator('.qa-answer-card')).toHaveCount(1)
      await page.reload()
      await expect(page.locator('.qa-answer-card')).toHaveCount(1)
      expect(requests).toBe(2)
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
      expect(errors).toEqual([])
    } finally {
      // Always unlock our held route; fixture teardown owns route disposal.
      // Do not replace the original test failure with a closed-page error.
      release()
      releaseSecond()
    }
  })
}
