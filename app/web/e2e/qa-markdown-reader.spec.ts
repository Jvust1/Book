import { expect, test } from '@playwright/test'

const course = 'synthetic_qa_course'
const sourceId = 'synthetic_verified_source'
const answer = '## 合成解答\n\n1. 取 **x = 3**\n2. 验证平方\n\n| 项目 | 数值 |\n| --- | --- |\n| x² | 9 |\n\n$$\nx^2=9\n$$\n\n```python\nx = 3\n```\n\n[附加链接](https://example.invalid/unverified)\n\n![外部图片](https://example.invalid/image.png)\n\n<script>throw new Error("must not run")</script>'
const citation = { evidence_id: 'synthetic-E1', source_kind: 'object', source_id: sourceId,
  chapter_id: 'synthetic_ch01', section_id: 'synthetic_s01', object_type: 'formula', type_zh: '公式',
  number: '1.1', title_zh: '合成已核验来源', title_en: null, printed_page: 1, pdf_page: 2, source_anchor: 'synthetic:p2' }

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`structured QA answer keeps citation round trip and inert resources (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize(viewport)
    let asks = 0
    const external: string[] = []
    const errors: string[] = []
    page.on('request', request => { if (request.url().includes('example.invalid')) external.push(request.url()) })
    page.on('pageerror', error => errors.push(error.message))
    await page.route('**/api/courses/**', async route => {
      const path = new URL(route.request().url()).pathname
      if (path.endsWith('/qa')) {
        asks++
        await route.fulfill({ json: { course_id: course, book_id: 'synthetic_book', question: route.request().postDataJSON().question,
          answer, answer_kind: 'generated', answer_style: 'explain', scope_requested: 'book', scope_used: 'book',
          insufficient_evidence: false, message: null, citations: [citation] } })
      } else if (path.includes('/sources/')) {
        await route.fulfill({ json: { ...citation, course_id: course, book_id: 'synthetic_book', kind: 'object', type: 'formula',
          content_zh: '原创测试来源', formula: 'x^2=9', source_batch: 'synthetic-test-only', translation_available: true,
          context_before: [], context_after: [] } })
      } else {
        await route.fulfill({ json: { course: { course_id: course, name_zh: '合成课程', name_en: null, authors: [],
          book_id: 'synthetic_book', chapter_count: 1, section_count: 1, runtime_status: 'READY' }, chapters: [], section_count: 1 } })
      }
    })
    await page.goto(`/courses/${course}/qa`)
    await page.getByRole('textbox', { name: '教材问题' }).fill('**问题原文**')
    await page.getByRole('button', { name: '提问', exact: true }).click()
    await expect(page.getByRole('heading', { name: '合成解答' })).toBeVisible()
    await expect(page.locator('.qa-markdown table')).toBeVisible()
    await expect(page.locator('.qa-markdown .katex')).toHaveCount(1)
    await expect(page.locator('.qa-markdown pre code')).toHaveText('x = 3')
    await expect(page.getByText('**问题原文**', { exact: true })).toBeVisible()
    await expect(page.locator('.qa-markdown a, .qa-markdown img, .qa-markdown script')).toHaveCount(0)
    await expect(page.getByText('图片未加载：外部图片', { exact: true })).toBeVisible()
    const verifiedLink = page.locator('.qa-citation-card').getByRole('link', { name: '查看教材来源' })
    await expect(verifiedLink).toHaveAttribute('href', `/courses/${course}/sources/object/${sourceId}`)
    await verifiedLink.click()
    await expect(page.getByText('PDF 页：2', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: '返回问答' }).click()
    await expect(page.getByRole('heading', { name: '合成解答' })).toBeVisible()
    expect(asks).toBe(1)
    await page.getByText('查看回答原文', { exact: true }).click()
    await expect(page.locator('.qa-original-answer pre')).toHaveText(answer)
    await page.getByText('查看回答原文', { exact: true }).click()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: `test-results/qa-markdown-pilot-${viewport.name}.png`, fullPage: true })
    expect(external).toEqual([])
    expect(errors).toEqual([])
  })
}
