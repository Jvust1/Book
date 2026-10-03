import { Buffer } from 'node:buffer'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'
import { syntheticPdf } from '../e2e/syntheticPdf'

// No route.fulfill or API mocks: an explicit test-only FastAPI process reads
// original temporary course/search/source files and uses real SQLite progress.
// Only generation is the existing deterministic provider; no paid model calls.
const course = 'original_algebra_pilot'
const section = 'original_s01'
const source = 'doubling_rule'
const sectionPath = `/courses/${course}/sections/${section}`
const sourcePath = `/courses/${course}/sources/object/${source}`
const qaPath = `/courses/${course}/qa?section=${section}`
const pageTexts = ['Original algebra pilot cover.', 'Doubling resonance: 2 plus 2 equals 4.']

function diagnostic(student: string) {
  const result = spawnSync('python', [resolve('../../tools/check_symbolic_answer.py')], {
    input: JSON.stringify({ student, expected: '4' }), encoding: 'utf8', timeout: 12_000,
    maxBuffer: 65_536, shell: false,
  })
  expect(result.error).toBeUndefined()
  expect(result.status, result.stderr).toBe(0)
  const payload = JSON.parse(result.stdout)
  expect(payload.schema_version).toBe('symbolic_diagnostic_v1')
  expect(payload.automatic_grade).toBe(false)
  return payload
}

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`original chapter study-to-source-to-QA-to-practice (${viewport.name})`, async ({ page, request, baseURL }) => {
    await page.setViewportSize(viewport)
    const errors: string[] = []
    const unexpectedWrites: string[] = []
    const sourceReads: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('request', req => {
      const url = new URL(req.url())
      if (url.pathname === `/api${sourcePath}`) sourceReads.push(req.url())
      if (url.origin !== new URL(baseURL!).origin || (req.method() !== 'GET' &&
        !url.pathname.includes('/study/') && url.pathname !== `/api/courses/${course}/qa`)) {
        unexpectedWrites.push(`${req.method()} ${url.pathname}`)
      }
    })
    await page.goto('/')
    await expect(page.getByRole('heading', { name: '教材库' })).toBeVisible()
    await expect(page.getByRole('link', { name: '进入课程' })).toHaveCount(1)
    await page.getByRole('link', { name: '进入课程' }).click()
    await page.getByRole('link', { name: '进入章节' }).click()
    await page.locator(`a[href="${sectionPath}"]`).click()
    await expect(page.getByRole('heading', { name: '原创倍增小节' })).toBeVisible()

    await page.getByRole('tab', { name: '预习', exact: true }).click()
    await expect(page.getByLabel('本节教材对象统计')).toBeVisible()
    await expect(page.locator('.learning-card .katex-mathml')).toHaveCount(1)
    await page.getByRole('tab', { name: '学习', exact: true }).click()
    const definition = page.locator('.learning-card').filter({ has: page.getByRole('heading', { name: '倍增规则', exact: true }) })
    await expect(definition.getByText(/原创试点：把一个数与自身相加/)).toBeVisible()
    await expect(definition.locator('.katex-mathml')).toHaveCount(3)
    await expect(page.getByText(/学习进度：/)).toBeVisible()
    const complete = page.getByRole('button', { name: '标记完成', exact: true })
    if (await complete.count()) await complete.click()
    await expect(page.getByText('学习进度：已完成', { exact: true })).toBeVisible()

    await definition.getByRole('link', { name: '查看教材来源' }).click()
    await expect(page).toHaveURL(new URL(sourcePath, baseURL).href)
    const facts = page.getByLabel('教材来源定位', { exact: true })
    await expect(facts.getByText('PDF 页：2', { exact: true })).toBeVisible()
    await expect(facts.getByText('教材页：1', { exact: true })).toBeVisible()
    await expect(facts.getByText('original:pdf:2:doubling_rule', { exact: true })).toBeVisible()
    const storageBeforePdf = await page.evaluate(() => [JSON.stringify(localStorage), JSON.stringify(sessionStorage)])
    await page.getByLabel('选择本地 PDF').setInputFiles({ name: 'original-algebra-pilot.pdf',
      mimeType: 'application/pdf', buffer: Buffer.from(syntheticPdf(2, pageTexts)) })
    await expect(page.getByRole('img', { name: '本地 PDF 第 2 页（文件身份未核验）' })).toBeVisible()
    const pdfSearch = page.getByRole('region', { name: '本地 PDF 文本查找' })
    await pdfSearch.getByLabel('提取起始页', { exact: true }).fill('2')
    await pdfSearch.getByLabel('提取结束页', { exact: true }).fill('2')
    await pdfSearch.getByRole('button', { name: '提取所选页文本', exact: true }).click()
    await expect(pdfSearch.getByText('已提取 PDF 第 2 至 2 页 · 共 1 页有文本', { exact: true })).toBeVisible()
    await pdfSearch.getByRole('textbox', { name: '本地查找词', exact: true }).fill('resonanse')
    await pdfSearch.getByRole('button', { name: '查找所选页', exact: true }).click()
    await expect(pdfSearch.locator('.pdf-search-results p')).toHaveText(pageTexts[1])
    await pdfSearch.getByRole('button', { name: '浏览本地 PDF 第 2 页', exact: true }).click()
    await expect(pdfSearch.getByText(/文件身份仍未核验；匹配结果不是教材引用或答案/)).toBeVisible()
    expect(await page.evaluate(() => [JSON.stringify(localStorage), JSON.stringify(sessionStorage)])).toEqual(storageBeforePdf)
    await page.screenshot({ path: `pilot-test-results/chapter-source-${viewport.name}.png`, fullPage: true })
    await page.getByRole('button', { name: '返回学习', exact: true }).click()
    await expect(page).toHaveURL(new URL(`${sectionPath}?mode=learn`, baseURL).href)

    await page.getByRole('link', { name: '问本节内容' }).click()
    await expect(page).toHaveURL(new URL(qaPath, baseURL).href)
    const answered = page.waitForResponse(response => response.url().endsWith(`/api/courses/${course}/qa`))
    await page.getByRole('textbox', { name: '教材问题' }).fill('倍增规则')
    await page.getByRole('button', { name: '提问', exact: true }).click()
    const answer = await (await answered).json()
    expect(answer.answer_kind).toBe('generated')
    expect(answer.scope_used).toBe('section')
    expect(answer.citations[0]).toMatchObject({ source_kind: 'object', source_id: source,
      section_id: section, pdf_page: 2, printed_page: 1, source_anchor: 'original:pdf:2:doubling_rule' })
    await expect(page.getByText('回答依据：提问时的小节', { exact: true })).toBeVisible()
    await expect(page.locator('.qa-markdown .katex-mathml')).toHaveCount(2)
    await page.screenshot({ path: `pilot-test-results/chapter-qa-${viewport.name}.png`, fullPage: true })
    await page.locator('.qa-citation-card').getByRole('link', { name: '查看教材来源' }).click()
    await expect(facts.getByText('结构化来源：object:doubling_rule', { exact: true })).toBeVisible()
    // Full identity reuses the verified session cache, but never the selected PDF.
    expect(sourceReads).toHaveLength(1)
    await expect(page.locator('.local-pdf-canvas canvas')).toHaveCount(0)
    await expect(pdfSearch).toHaveCount(0)
    await page.getByRole('button', { name: '返回问答', exact: true }).click()
    await expect(page.locator('.qa-citation-card[aria-current="true"]')).toHaveCount(1)
    // Reload resets module state, but a follow-up must retain unique message IDs.
    await page.reload()
    await expect(page.locator('.qa-answer-card')).toHaveCount(1)
    const followUp = page.waitForResponse(response => response.url().endsWith(`/api/courses/${course}/qa`))
    await page.getByRole('textbox', { name: '教材问题' }).fill('倍增规则')
    await page.getByRole('button', { name: '提问', exact: true }).click()
    expect((await (await followUp).json()).answer_kind).toBe('generated')
    await expect(page.locator('.qa-answer-card')).toHaveCount(2)
    const messageIds = await page.evaluate(courseId => {
      const state = JSON.parse(sessionStorage.getItem(`book:qa-session:${courseId}`)!)
      return state.messages.map((message: { id: string }) => message.id) as string[]
    }, course)
    expect(messageIds).toHaveLength(4)
    expect(new Set(messageIds).size).toBe(messageIds.length)
    await page.getByRole('link', { name: '← 返回课程' }).click()
    await page.getByRole('link', { name: '进入章节' }).click()
    await page.locator(`a[href="${sectionPath}"]`).click()
    await page.getByRole('tab', { name: '复习', exact: true }).click()
    await expect(page.locator('.learning-card')).toHaveCount(1)
    await page.getByRole('button', { name: '显示内容', exact: true }).click()
    await expect(page.getByText(/原创试点：把一个数与自身相加/)).toBeVisible()
    await page.getByRole('tab', { name: '刷题', exact: true }).click()
    await expect(page.getByRole('heading', { name: '倍增练习', exact: true })).toBeVisible()
    await expect(page.getByText('学习进度：进行中', { exact: true })).toBeVisible()
    const progressBefore = await (await request.get(`/api/courses/${course}/study-records`)).json()
    await page.getByRole('textbox', { name: '算式', exact: true }).fill('2+2')
    await page.getByRole('button', { name: '计算', exact: true }).click()
    const result = page.getByLabel('演算结果', { exact: true })
    await expect(result).toHaveText('4')
    // Explicit CLI integration gate, not a browser endpoint or automatic grade.
    expect(diagnostic(await result.innerText()).equivalent).toBe(true)
    expect(diagnostic('5').equivalent).toBe(false)
    expect(diagnostic('__import__("os")').equivalent).toBeNull()
    expect(await (await request.get(`/api/courses/${course}/study-records`)).json()).toEqual(progressBefore)
    await expect(page.getByText('教材数据中暂未提供解析', { exact: true })).toBeVisible()
    await page.screenshot({ path: `pilot-test-results/chapter-practice-${viewport.name}.png`, fullPage: true })
    await page.getByRole('tab', { name: '学习', exact: true }).click()
    await page.getByRole('tab', { name: '刷题', exact: true }).click()
    await expect(page.getByRole('textbox', { name: '算式', exact: true })).toHaveValue('')
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    expect(unexpectedWrites).toEqual([])
    expect(errors).toEqual([])
  })
}
