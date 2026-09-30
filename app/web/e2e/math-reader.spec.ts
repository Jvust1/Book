import { expect, test, type Page } from '@playwright/test'

// Original synthetic chapter fixture. No textbook full text is added or uploaded.
const course = 'synthetic_math_course'
const section = 'synthetic_ch01_s01'
const sourceId = 'synthetic_square_identity'
const formula = String.raw`\frac{1}{2} + \sum_{k=1}^{8} k^2 = \frac{409}{2}`
const prose = String.raw`示例取 \(x=3\)，得到 \(x^2=9\)。价格 $5 和 $10 保持原文。`
const item = {
  kind: 'object', source_id: sourceId, object_type: 'formula', type_zh: '公式',
  number: '1.1', title_zh: '合成公式示例', title_en: null, formula,
  printed_page: 7, pdf_page: 11, content_zh: prose, translation_available: true,
}

async function fixtureApi(page: Page, content = prose) {
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname
    let body: unknown
    if (path.endsWith(`/sections/${section}`)) {
      body = { course_id: course, book_id: 'synthetic_book', chapter_id: 'synthetic_ch01',
        section: { section_id: section, number: '1.1', title_zh: '合成章节试点', title_en: null,
          printed_page_start: 7, printed_page_end: 7, pdf_page_start: 11, pdf_page_end: 11 },
        object_count: 1, figure_count: 0, translation_available: true }
    } else if (path.includes('/sources/')) {
      body = { ...item, content_zh: content, course_id: course, book_id: 'synthetic_book', section_id: section,
        type: 'formula', source_anchor: 'synthetic:page-11:formula-1', source_batch: 'synthetic-test-only',
        context_before: [], context_after: [] }
    } else if (path.includes('/study/')) {
      const mode = path.split('/').at(-2)
      body = { course_id: course, book_id: 'synthetic_book', section_id: section, mode,
        status: path.endsWith('/complete') ? 'completed' : 'in_progress',
        progress: path.endsWith('/complete') ? 100 : 0,
        started_at: '2026-09-30T00:00:00Z', last_studied_at: '2026-09-30T00:00:00Z',
        completed_at: null, updated_at: '2026-09-30T00:00:00Z' }
    } else {
      body = { mode: path.split('/').at(-1), course_id: course, book_id: 'synthetic_book',
        chapter_id: 'synthetic_ch01', section_id: section, source_status: 'available',
        items: [{ ...item, content_zh: content }], source_refs: [{ kind: item.kind, source_id: sourceId }] }
    }
    await route.fulfill({ json: body })
  })
}

test('synthetic chapter renders four modes and retains source identity on return', async ({ page }) => {
  await fixtureApi(page)
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto(`/courses/${course}/sections/${section}?mode=learn`)
  await expect(page.locator('.learning-card .katex')).toHaveCount(3)
  await expect(page.locator('.learning-card math')).toHaveCount(3)
  await page.getByText('查看公式原文', { exact: true }).click()
  await expect(page.locator('.math-source code')).toHaveText(formula)
  await page.getByRole('tab', { name: '预习', exact: true }).click()
  await expect(page.locator('.learning-card .katex')).toHaveCount(1)
  await page.getByRole('tab', { name: '刷题', exact: true }).click()
  await expect(page.locator('.learning-card .katex')).toHaveCount(3)
  await expect(page.getByText('教材数据中暂未提供解析')).toBeVisible()
  await page.getByRole('tab', { name: '复习', exact: true }).click()
  await expect(page.locator('.learning-card .katex')).toHaveCount(1)
  await page.getByRole('button', { name: '显示内容' }).click()
  await expect(page.locator('.learning-card .katex')).toHaveCount(3)
  await page.getByRole('link', { name: '查看教材来源' }).click()
  await expect(page.getByText('PDF 页：11', { exact: true })).toBeVisible()
  await expect(page.getByText('教材页：7', { exact: true })).toBeVisible()
  await expect(page.getByText('synthetic:page-11:formula-1', { exact: true })).toBeVisible()
  await expect(page.locator('.source-page .katex')).toHaveCount(3)
  await page.getByRole('button', { name: '返回学习' }).click()
  await expect(page).toHaveURL(/mode=review$/)
  await expect(page.locator('.learning-card .katex')).toHaveCount(3)
  await page.reload()
  await expect(page.locator('.learning-card .katex')).toHaveCount(3)
  expect(errors).toEqual([])
})

test('narrow reader contains wide equations and ignores unsafe markup', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const content = String.raw`<img src="https://example.invalid/track" onerror="alert(1)"> \(\badcommand{x}\) \(\includegraphics{https://example.invalid/image}\) \(\href{javascript:alert(1)}{click}\)`
  await fixtureApi(page, content)
  const externalRequests: string[] = []
  page.on('request', request => {
    if (request.url().includes('example.invalid')) externalRequests.push(request.url())
  })
  await page.goto(`/courses/${course}/sections/${section}?mode=learn`)
  await expect(page.locator('.learning-card .katex-display')).toHaveCount(1)
  await expect(page.getByText('部分公式暂无法排版，已保留原文')).toBeVisible()
  expect(await page.locator('.learning-content img, .learning-content a, .learning-content script').count()).toBe(0)
  expect(externalRequests).toEqual([])
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: 'test-results/math-reader-narrow.png', fullPage: true })
})
