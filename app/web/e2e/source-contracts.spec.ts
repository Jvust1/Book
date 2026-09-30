import { expect, test, type Page } from '@playwright/test'

const course = 'synthetic_contract_course'
const sourceId = 'original_source'
const errorMessage = '教材响应校验失败，请刷新后重试'
const courseResponse = { course: { course_id: course, name_zh: '原创契约验收课程', name_en: null, authors: [],
  book_id: 'synthetic_book', chapter_count: 1, section_count: 1, runtime_status: 'READY' }, chapters: [], section_count: 1 }
const citation = { evidence_id: 'E1', source_kind: 'object', source_id: sourceId, chapter_id: 'ch1', section_id: 's1',
  object_type: 'definition', type_zh: '定义', number: '1', title_zh: '原创已核验来源', title_en: null,
  printed_page: 'iv', pdf_page: 3, source_anchor: 'synthetic:page3' }
const source = { course_id: course, book_id: 'synthetic_book', section_id: 's1', kind: 'object', source_id: sourceId,
  type: 'definition', type_zh: '定义', number: '1', title_zh: '原创已核验来源', title_en: null,
  content_zh: 'Original synthetic source.', formula: null, printed_page: 'iv', pdf_page: 3,
  source_anchor: 'synthetic:page3', source_batch: 'synthetic-only', translation_available: true, context_before: [], context_after: [] }
const answer = (question: string) => ({ course_id: course, book_id: 'synthetic_book', question,
  answer: 'Original validated answer.', answer_kind: 'generated', answer_style: 'brief', scope_requested: 'book', scope_used: 'book',
  insufficient_evidence: false, message: null, citations: [citation] })

async function basicApi(page: Page) {
  await page.route(`**/api/courses/${course}`, route => route.fulfill({ json: courseResponse }))
  await page.route(`**/api/courses/${course}/sources/object/${sourceId}`, route => route.fulfill({ json: source }))
}

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`Zod rejects uncited replies then validates QA source round trip (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize(viewport)
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    await basicApi(page)
    let asks = 0
    await page.route(`**/api/courses/${course}/qa`, route => {
      asks++
      const response = answer(route.request().postDataJSON().question)
      return route.fulfill({ json: asks === 1 ? { ...response, answer: 'UNVERIFIED_ANSWER', citations: [] } : response })
    })
    await page.goto(`/courses/${course}/qa`)
    await page.getByRole('textbox', { name: '教材问题' }).fill('Original malformed reply test?')
    await page.getByRole('button', { name: '提问', exact: true }).click()
    await expect(page.getByRole('alert').getByRole('heading', { name: '问答暂未完成', exact: true })).toBeVisible()
    await expect(page.getByRole('alert').locator('p')).toHaveText(errorMessage)
    await expect(page.getByText('UNVERIFIED_ANSWER', { exact: true })).toHaveCount(0)
    await expect(page.locator('.qa-citation-card')).toHaveCount(0)
    expect(await page.evaluate(() => JSON.stringify(sessionStorage))).not.toContain('UNVERIFIED_ANSWER')

    await page.getByRole('textbox', { name: '教材问题' }).fill('Original valid retry?')
    await page.getByRole('button', { name: '提问', exact: true }).click()
    await expect(page.locator('.qa-markdown')).toHaveText('Original validated answer.')
    await expect(page.getByRole('alert')).toHaveCount(0)
    const link = page.locator('.qa-citation-card').getByRole('link', { name: '查看教材来源' })
    await expect(link).toHaveAttribute('href', `/courses/${course}/sources/object/${sourceId}`)
    await link.click()
    await expect(page.getByText('PDF 页：3', { exact: true })).toBeVisible()
    await expect(page.getByText('教材页：iv', { exact: true })).toBeVisible()
    await expect(page.getByText('synthetic:page3', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '返回问答', exact: true }).click()
    await expect(page.locator('.qa-markdown')).toHaveText('Original validated answer.')
    expect(asks).toBe(2)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: `test-results/zod-source-contract-${viewport.name}.png`, fullPage: true })
    expect(errors).toEqual([])
  })
}

test('wrong-source payload cannot open a reader or local PDF panel and reload recovers', async ({ page }) => {
  let corrupt = true
  await page.route(`**/api/courses/${course}/sources/object/${sourceId}`, route => route.fulfill({
    json: corrupt ? { ...source, source_id: 'wrong_source', content_zh: 'UNRELATED_SOURCE' } : source,
  }))
  await page.goto(`/courses/${course}/sources/object/${sourceId}`)
  await expect(page.getByRole('alert')).toContainText(errorMessage)
  await expect(page.getByText('UNRELATED_SOURCE', { exact: true })).toHaveCount(0)
  await expect(page.getByRole('region', { name: '本地 PDF 来源预览' })).toHaveCount(0)
  corrupt = false
  await page.reload()
  await expect(page.getByText('Original synthetic source.', { exact: true })).toBeVisible()
  await expect(page.getByRole('region', { name: '本地 PDF 来源预览' })).toBeVisible()
})

test('wrong-course search results fail closed and a new query restores source navigation', async ({ page }) => {
  await basicApi(page)
  await page.route(`**/api/courses/${course}/search?*`, route => {
    const query = new URL(route.request().url()).searchParams.get('q')!
    return route.fulfill({ json: { course_id: query === 'invalid' ? 'wrong_course' : course, book_id: 'synthetic_book',
      query, result_count: 1, results: [{ rank: 1, score: 1, source_kind: 'object', source_id: sourceId,
        object_type: 'definition', number: '1', title_zh: '原创已核验来源', title_en: null, formula: null,
        pdf_page: 3, printed_page: 'iv', source_anchor: 'synthetic:page3', snippet: 'Original search snippet.' }] } })
  })
  await page.goto(`/courses/${course}/search?q=invalid`)
  await expect(page.getByRole('alert').getByRole('heading', { name: '搜索失败', exact: true })).toBeVisible()
  await expect(page.getByRole('alert').locator('p')).toHaveText(errorMessage)
  await expect(page.locator('.search-results')).toHaveCount(0)
  await page.getByRole('searchbox', { name: '教材搜索词' }).fill('valid')
  await page.getByRole('button', { name: '搜索', exact: true }).click()
  const link = page.locator('.search-results').getByRole('link', { name: '查看教材来源' })
  await expect(link).toHaveAttribute('href', `/courses/${course}/sources/object/${sourceId}`)
  await link.click()
  await expect(page.getByText('PDF 页：3', { exact: true })).toBeVisible()
})
