import { expect, test, type Page } from '@playwright/test'

const course = 'synthetic_cache_course'
const alpha = 'CACHE_SOURCE_ALPHA'
const beta = 'CACHE_SOURCE_BETA'
const sourcePath = (id: string) => `/courses/${course}/sources/object/${id}`
const makeSource = (id: string, content?: string) => ({ course_id: course, book_id: 'synthetic_cache_book',
  section_id: 's1', kind: 'object', source_id: id, type: 'definition', type_zh: '定义', number: id === 'source_a' ? '1' : '2',
  title_zh: id === 'source_a' ? '原创来源甲' : '原创来源乙', title_en: null,
  content_zh: content ?? (id === 'source_a' ? alpha : beta), formula: null,
  printed_page: id === 'source_a' ? 'iv' : 5, pdf_page: id === 'source_a' ? 3 : 4,
  source_anchor: `synthetic:${id}`, source_batch: 'synthetic-only', translation_available: true,
  context_before: [], context_after: [] })

async function fixture(page: Page) {
  const state = { mode: 'ok' as 'ok' | 'network' | 'invalid' | 'forbidden', sourceReads: [] as string[], searches: 0, posts: [] as string[] }
  page.on('request', request => { if (request.method() !== 'GET') state.posts.push(request.url()) })
  await page.route(`**/api/courses/${course}`, route => route.fulfill({ json: {
    course: { course_id: course, name_zh: '原创缓存验收课程', name_en: null, authors: [], book_id: 'synthetic_cache_book',
      chapter_count: 1, section_count: 1, runtime_status: 'READY' }, chapters: [], section_count: 1,
  } }))
  await page.route(`**/api/courses/${course}/search?*`, route => {
    state.searches++
    if (state.mode === 'network') return route.abort('connectionfailed')
    const query = new URL(route.request().url()).searchParams.get('q')!
    return route.fulfill({ json: { course_id: course, book_id: 'synthetic_cache_book', query, result_count: 2,
      results: ['source_a', 'source_b'].map((id, index) => ({ rank: index + 1, score: 1, source_kind: 'object', source_id: id,
        object_type: 'definition', number: String(index + 1), title_zh: index ? '原创来源乙' : '原创来源甲', title_en: null,
        formula: null, pdf_page: index + 3, printed_page: index ? 5 : 'iv', source_anchor: `synthetic:${id}`, snippet: 'Original search snippet.' })) } })
  })
  await page.route(`**/api/courses/${course}/sources/object/*`, route => {
    const id = new URL(route.request().url()).pathname.split('/').at(-1)!
    state.sourceReads.push(id)
    if (state.mode === 'network') return route.abort('connectionfailed')
    if (state.mode === 'forbidden') return route.fulfill({ status: 403, json: { error: { code: 'forbidden', message: '合成来源访问被拒绝' } } })
    return route.fulfill({ json: state.mode === 'invalid' ? { ...makeSource(id), course_id: 'wrong_course' } : makeSource(id) })
  })
  return state
}

async function openFromResults(page: Page, id: string) {
  await page.locator(`.search-result-card[data-source-key="object:${id}"]`).getByRole('link', { name: '查看教材来源' }).click()
  await expect(page.getByText(id === 'source_a' ? alpha : beta, { exact: true })).toBeVisible()
  await expect(page).toHaveURL(new RegExp(`${sourcePath(id)}$`))
}

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`validated memory cache survives API interruption and fails closed on invalid refresh (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize(viewport)
    const state = await fixture(page)
    const errors: string[] = []; page.on('pageerror', error => errors.push(error.message))
    await page.goto(`/courses/${course}/search?q=original`)
    const localBefore = await page.evaluate(() => JSON.stringify(localStorage))
    await expect(page.locator('.search-result-card')).toHaveCount(2)
    await openFromResults(page, 'source_a')
    await page.getByRole('button', { name: '返回搜索', exact: true }).click()
    await openFromResults(page, 'source_b')
    expect(state.searches).toBe(1)
    expect(state.sourceReads).toEqual(['source_a', 'source_b'])
    state.mode = 'network'
    await page.getByRole('button', { name: '返回搜索', exact: true }).click()
    await expect(page.getByText('显示本次会话缓存。', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '重新读取', exact: true }).click()
    await expect(page.getByText('网络中断，当前显示本次会话缓存；内容可能已更新。', { exact: true })).toBeVisible()
    await expect(page.locator('.search-result-card')).toHaveCount(2)
    expect(state.searches).toBe(2)
    await openFromResults(page, 'source_a')
    await expect(page.getByText('显示本次会话缓存。', { exact: true })).toBeVisible()
    await expect(page.getByText(beta, { exact: true })).toHaveCount(0)
    expect(state.sourceReads).toEqual(['source_a', 'source_b'])
    expect(state.searches).toBe(2)

    await page.getByRole('button', { name: '重新读取', exact: true }).click()
    await expect(page.getByText('网络中断，当前显示本次会话缓存；内容可能已更新。', { exact: true })).toBeVisible()
    await expect(page.getByText(alpha, { exact: true })).toBeVisible()
    await expect(page.getByText('PDF 页：3', { exact: true })).toBeVisible()
    await expect(page.getByText('教材页：iv', { exact: true })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: `test-results/tanstack-reader-cache-${viewport.name}.png`, fullPage: true })

    state.mode = 'invalid'
    await page.getByRole('button', { name: '重新读取', exact: true }).click()
    await expect(page.getByRole('alert').locator('p')).toHaveText('教材响应校验失败，请刷新后重试')
    await expect(page.getByText(alpha, { exact: true })).toHaveCount(0)
    await expect(page.getByRole('region', { name: '本地 PDF 来源预览' })).toHaveCount(0)
    state.mode = 'ok'
    await page.getByRole('button', { name: '重新读取', exact: true }).click()
    await expect(page.getByText(alpha, { exact: true })).toBeVisible()
    await expect(page.getByRole('alert')).toHaveCount(0)
    expect(await page.evaluate(() => JSON.stringify(localStorage))).toBe(localBefore)
    const stored = await page.evaluate(() => JSON.stringify(sessionStorage))
    expect(stored).not.toContain(alpha); expect(stored).not.toContain(beta)

    // New app lifetime: no persisted source cache can mask the unavailable API.
    state.mode = 'network'
    await page.reload()
    await expect(page.getByRole('alert')).toContainText('教材来源加载失败')
    await expect(page.getByText(alpha, { exact: true })).toHaveCount(0)
    await expect(page.getByText('显示本次会话缓存。', { exact: true })).toHaveCount(0)
    expect(state.posts).toEqual([])
    expect(errors).toEqual([])
  })
}

test('a server authorization denial never falls back to the previous source cache', async ({ page }) => {
  const state = await fixture(page)
  await page.goto(sourcePath('source_a'))
  await expect(page.getByText(alpha, { exact: true })).toBeVisible()
  state.mode = 'forbidden'
  await page.getByRole('button', { name: '重新读取', exact: true }).click()
  await expect(page.getByRole('alert').locator('p')).toHaveText('合成来源访问被拒绝')
  await expect(page.getByText(alpha, { exact: true })).toHaveCount(0)
  await expect(page.getByRole('region', { name: '本地 PDF 来源预览' })).toHaveCount(0)
  expect(state.sourceReads).toEqual(['source_a', 'source_a'])
})

test('cancel abandons a held source request and a later explicit read recovers', async ({ page }) => {
  let held = true; let count = 0
  let release!: () => void; let completed!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  const abandonedFinished = new Promise<void>(resolve => { completed = resolve })
  await page.route(`**/api${sourcePath('source_a')}`, async route => {
    count++
    if (held) {
      await gate
      try { await route.fulfill({ json: makeSource('source_a', 'ABANDONED_SOURCE_VALUE') }) } catch { /* Fetch was cancelled. */ }
      finally { completed() }
    } else await route.fulfill({ json: makeSource('source_a') })
  })
  try {
    await page.goto(sourcePath('source_a'))
    await expect.poll(() => count).toBe(1)
    await page.getByRole('button', { name: '取消读取', exact: true }).click()
    await expect(page.getByText('读取已停止，请重新读取', { exact: true })).toBeVisible()
    held = false; release(); await abandonedFinished
    await expect(page.getByText('ABANDONED_SOURCE_VALUE', { exact: true })).toHaveCount(0)
    await page.getByRole('button', { name: '重新读取', exact: true }).click()
    await expect(page.getByText(alpha, { exact: true })).toBeVisible()
    await expect(page.getByText('ABANDONED_SOURCE_VALUE', { exact: true })).toHaveCount(0)
    expect(count).toBe(2)
  } finally { release() }
})
