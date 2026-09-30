import { expect, test, type Page } from '@playwright/test'

const course = 'original_contract_course'
const sectionId = 'original_contract_section'
const identity = { course_id: course, book_id: 'original_contract_book', chapter_id: 'original_chapter' }
const section = { ...identity, section: { section_id: sectionId, number: '1', title_zh: '原创契约试点', title_en: null,
  printed_page_start: 'iv', printed_page_end: 'iv', pdf_page_start: 2, pdf_page_end: 2 },
  object_count: 1, figure_count: 0, translation_available: true }
const item = { kind: 'object', source_id: 'original_source', object_type: 'definition', type_zh: '定义', number: '1.1',
  title_zh: '仅正确响应可显示', title_en: null, formula: 'x+x=2x', content_zh: '原创且身份一致的内容。',
  printed_page: 'iv', pdf_page: 2, translation_available: true }

async function fixtures(page: Page, corrupt: 'section-course' | 'mode-course' | 'mode-name' | 'source-ref' | 'book') {
  const writes: string[] = []
  await page.route(`**/api/courses/${course}/**`, async route => {
    const path = new URL(route.request().url()).pathname
    if (path.includes('/study/')) {
      writes.push(path)
      return route.fulfill({ json: { course_id: course, book_id: identity.book_id, section_id: sectionId,
        mode: path.split('/').at(-2), status: 'in_progress', progress: 0,
        started_at: '2026-09-30T00:00:00Z', last_studied_at: '2026-09-30T00:00:00Z',
        completed_at: null, updated_at: '2026-09-30T00:00:00Z' } })
    }
    if (path.endsWith(`/sections/${sectionId}`)) return route.fulfill({ json: {
      ...section, ...(corrupt === 'section-course' ? { course_id: 'wrong_course' } : {}),
    } })
    const mode = path.split('/').at(-1)
    const body = { ...identity, section_id: sectionId, mode, source_status: 'available',
      items: [item], source_refs: [{ kind: 'object', source_id: item.source_id }] }
    return route.fulfill({ json: mode !== 'learn' ? body : { ...body,
      ...(corrupt === 'mode-course' ? { course_id: 'wrong_course' } : {}),
      ...(corrupt === 'mode-name' ? { mode: 'practice' } : {}),
      ...(corrupt === 'source-ref' ? { source_refs: [] } : {}),
      ...(corrupt === 'book' ? { book_id: 'wrong_book' } : {}),
    } })
  })
  return writes
}

test('rejects a Section from another course without showing its learning content or writing progress', async ({ page }) => {
  const writes = await fixtures(page, 'section-course')
  await page.goto(`/courses/${course}/sections/${sectionId}?mode=learn`)
  await expect(page.getByRole('heading', { name: '小节加载失败', exact: true })).toBeVisible()
  await expect(page.getByText('教材响应校验失败，请刷新后重试', { exact: true })).toBeVisible()
  await expect(page.locator('.learning-card')).toHaveCount(0)
  expect(writes).toEqual([])
})

for (const corrupt of ['mode-course', 'mode-name', 'source-ref', 'book'] as const) {
  test(`fails closed on ${corrupt} and recovers only after a valid mode response`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    const writes = await fixtures(page, corrupt)
    await page.goto(`/courses/${course}/sections/${sectionId}?mode=learn`)
    await expect(page.getByRole('heading', { name: '学习内容加载失败', exact: true })).toBeVisible()
    await expect(page.locator('.learning-card')).toHaveCount(0)
    await expect(page.getByRole('region', { name: '本地演算辅助' })).toHaveCount(0)
    expect(writes).toEqual([])
    if (corrupt === 'source-ref') await page.screenshot({ path: 'test-results/zod-learning-rejection-narrow.png', fullPage: true })
    await page.getByRole('tab', { name: '预习', exact: true }).click()
    await expect(page.getByRole('heading', { name: item.title_zh, exact: true })).toBeVisible()
    await expect(page.getByText('学习进度：进行中', { exact: true })).toBeVisible()
    await expect(page.getByRole('link', { name: '查看教材来源' })).toHaveAttribute('href', `/courses/${course}/sources/object/${item.source_id}`)
    await expect(page.getByRole('alert')).toHaveCount(0)
    expect(writes).toEqual([`/api/courses/${course}/sections/${sectionId}/study/preview/touch`])
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    expect(errors).toEqual([])
  })
}
