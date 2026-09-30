import { expect, test, type Page } from '@playwright/test'

async function openPractice(page: Page) {
  await page.route('**/api/courses/**', route => {
    const path = new URL(route.request().url()).pathname
    const identity = { course_id: 'synthetic_practice', book_id: 'synthetic_book', section_id: 'synthetic_s01' }
    if (path.endsWith('/sections/synthetic_s01')) return route.fulfill({ json: { ...identity, chapter_id: 'synthetic_ch01',
      section: { section_id: 'synthetic_s01', number: '1.1', title_zh: '合成练习试点', title_en: null,
        printed_page_start: 1, printed_page_end: 1, pdf_page_start: 2, pdf_page_end: 2 },
      object_count: 1, figure_count: 0, translation_available: true } })
    if (path.includes('/study/')) return route.fulfill({ json: { ...identity, mode: path.split('/').at(-2), status: 'in_progress', progress: 0,
      started_at: '2026-09-30T00:00:00Z', last_studied_at: '2026-09-30T00:00:00Z', completed_at: null, updated_at: '2026-09-30T00:00:00Z' } })
    return route.fulfill({ json: { ...identity, chapter_id: 'synthetic_ch01', mode: path.split('/').at(-1), source_status: 'available',
      items: [{ kind: 'object', source_id: 'synthetic_exercise', object_type: 'exercise', type_zh: '练习', number: '1',
        title_zh: '原创测试练习', title_en: null, formula: null, printed_page: 1, pdf_page: 2,
        content_zh: '请使用自己的方法核对数值。', translation_available: true }],
      source_refs: [{ kind: 'object', source_id: 'synthetic_exercise' }] } })
  })
  await page.goto('/courses/synthetic_practice/sections/synthetic_s01?mode=learn')
  await expect(page.getByRole('heading', { name: '合成练习试点' })).toBeVisible()
  await expect(page.getByRole('region', { name: '本地演算辅助' })).toHaveCount(0)
  await page.getByRole('tab', { name: '刷题', exact: true }).click()
  await expect(page.getByRole('region', { name: '本地演算辅助' })).toBeVisible()
}

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`real math.js worker arithmetic, matrix and mode cleanup (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize(viewport)
    const errors: string[] = []
    const unexpectedPosts: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('request', request => {
      if (request.method() === 'POST' && !request.url().includes('/study/')) unexpectedPosts.push(request.url())
    })
    await openPractice(page)
    const storageBefore = await page.evaluate(() => [JSON.stringify(sessionStorage), JSON.stringify(localStorage)])
    await page.getByRole('button', { name: '行列式示例' }).click()
    await expect(page.getByLabel('演算结果')).toHaveCount(0)
    await page.getByRole('button', { name: '计算', exact: true }).click()
    await expect(page.getByLabel('演算结果')).toHaveText('-2')
    await expect(page.getByText('教材数据中暂未提供解析', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '逆矩阵示例' }).click()
    await page.getByRole('button', { name: '计算', exact: true }).click()
    await expect(page.getByLabel('演算结果')).toHaveText('[[0.6, -0.7], [-0.2, 0.4]]')
    await expect(page.getByText('由 mathjs@15.2.0 在本机计算', { exact: true })).toBeVisible()
    expect(await page.evaluate(() => [JSON.stringify(sessionStorage), JSON.stringify(localStorage)])).toEqual(storageBefore)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: `test-results/mathjs-practice-pilot-${viewport.name}.png`, fullPage: true })
    await page.getByRole('textbox', { name: '算式', exact: true }).fill('import("not-allowed")')
    await page.getByRole('button', { name: '计算', exact: true }).click()
    await expect(page.getByText('超出支持范围，请使用数值、小矩阵和列出的函数', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '三角函数示例' }).click()
    await page.getByRole('button', { name: '计算', exact: true }).click()
    await expect(page.getByLabel('演算结果')).toHaveText('1')
    await page.getByRole('tab', { name: '学习', exact: true }).click()
    await expect(page.getByRole('region', { name: '本地演算辅助' })).toHaveCount(0)
    await page.getByRole('tab', { name: '刷题', exact: true }).click()
    await expect(page.getByRole('textbox', { name: '算式', exact: true })).toHaveValue('')
    await expect(page.getByLabel('演算结果')).toHaveCount(0)
    expect(unexpectedPosts).toEqual([])
    expect(errors).toEqual([])
  })
}

test.describe('interrupted worker network', () => {
// A service worker must not fulfill the deliberately intercepted network request.
test.use({ serviceWorkers: 'block' })
test('cancels interrupted worker startup and then recovers with a fresh real worker', async ({ page }) => {
  let release!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  let arrived!: () => void
  const requested = new Promise<void>(resolve => { arrived = resolve })
  const pattern = /\/(?:src\/practice\/calculator\.worker\.ts|assets\/calculator\.worker-[^/]+\.js)(?:\?|$)/
  await page.route(pattern, async route => {
    arrived()
    await gate
    try { await route.continue() } catch { /* A terminated worker can abandon its fetch. */ }
  })
  await openPractice(page)
  await page.getByRole('textbox', { name: '算式', exact: true }).fill('1+1')
  await page.getByRole('button', { name: '计算', exact: true }).click()
  await requested
  await page.getByRole('button', { name: '取消计算', exact: true }).click()
  await expect(page.getByText('已取消，输入仍保留', { exact: true })).toBeVisible()
  await expect(page.getByRole('textbox', { name: '算式', exact: true })).toHaveValue('1+1')
  release()
  await page.unroute(pattern)
  await page.getByRole('textbox', { name: '算式', exact: true }).fill('2+2')
  await page.getByRole('button', { name: '计算', exact: true }).click()
  await expect(page.getByLabel('演算结果')).toHaveText('4')
  await page.getByRole('button', { name: '清空演算区', exact: true }).click()
  await expect(page.getByRole('textbox', { name: '算式', exact: true })).toHaveValue('')
  await expect(page.getByLabel('演算结果')).toHaveCount(0)
})

})
