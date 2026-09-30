import { Buffer } from 'node:buffer'
import { expect, test, type Page } from '@playwright/test'
import { syntheticPdf } from './syntheticPdf'

async function openSource(page: Page, pdfPage: number | null = 2) {
  await page.route('**/api/courses/**', route => route.fulfill({ json: {
    course_id: 'synthetic_course', book_id: 'synthetic_book', section_id: 'synthetic_s01',
    kind: 'object', source_id: 'synthetic_source', type: 'formula', type_zh: '公式', number: '1',
    title_zh: '合成来源页试点', title_en: null, content_zh: '仅用于工程验收的原创示例。',
    formula: 'x^2=9', printed_page: 1, pdf_page: pdfPage, source_anchor: 'synthetic:source-2',
    source_batch: 'synthetic-test-only', translation_available: true, context_before: [], context_after: [],
  } }))
  await page.goto('/courses/synthetic_course/sources/object/synthetic_source')
  await expect(page.getByRole('heading', { name: '对照本地 PDF' })).toBeVisible()
}
const file = { name: 'synthetic-chapter.pdf', mimeType: 'application/pdf', buffer: Buffer.from(syntheticPdf()) }

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`real PDF.js local source rendering, navigation and close (${viewport.name})`, async ({ page }) => {
    await page.setViewportSize(viewport)
    const requests: string[] = []
    const errors: string[] = []
    page.on('request', request => {
      if (request.method() !== 'GET' || !request.url().startsWith('http://127.0.0.1:5173/')) requests.push(request.url())
    })
    page.on('pageerror', error => errors.push(error.message))
    await openSource(page)
    await page.getByLabel('选择本地 PDF').setInputFiles(file)
    const canvas = page.getByRole('img', { name: '本地 PDF 第 2 页（文件身份未核验）' })
    await expect(canvas).toBeVisible()
    await expect(page.getByText('正在显示 PDF 页…')).toHaveCount(0)
    await page.getByText('本页可提取文本（辅助，最多 50,000 字符）', { exact: true }).click()
    await expect(page.getByText('Synthetic source pilot page 2', { exact: true })).toBeVisible()
    const inkPixels = await canvas.evaluate(element => {
      const canvas = element as HTMLCanvasElement
      const pixels = canvas.getContext('2d')!.getImageData(0, 0, canvas.width, canvas.height).data
      let count = 0
      for (let i = 0; i < pixels.length; i += 4) if (pixels[i] < 100 && pixels[i + 3] > 0) count++
      return count
    })
    expect(inkPixels).toBeGreaterThan(100)
    await page.getByRole('button', { name: '下一页' }).click()
    await expect(page.getByText('Synthetic source pilot page 3', { exact: true })).toBeVisible()
    await expect(page.getByText('当前浏览页不是教材标注的来源页。')).toBeVisible()
    await page.getByRole('button', { name: '回到来源页' }).click()
    await expect(page.getByText('Synthetic source pilot page 2', { exact: true })).toBeVisible()
    const beforeZoom = await canvas.evaluate(element => (element as HTMLCanvasElement).width)
    await page.getByLabel('PDF 缩放').selectOption('2')
    await expect.poll(() => canvas.evaluate(element => (element as HTMLCanvasElement).width)).toBeGreaterThan(beforeZoom)
    await expect(page.getByText('正在显示 PDF 页…')).toHaveCount(0)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: `test-results/pdfjs-pilot-${viewport.name}.png`, fullPage: true })
    await page.getByRole('button', { name: '关闭本地 PDF' }).click()
    await expect(page.locator('.local-pdf-canvas canvas')).toHaveCount(0)
    await expect(page.getByText(/本地文件：/)).toHaveCount(0)
    await page.reload()
    await expect(page.locator('.local-pdf-canvas canvas')).toHaveCount(0)
    expect(requests).toEqual([])
    expect(errors).toEqual([])
  })
}

test('invalid source mapping and corrupt PDF stay explicit, recoverable and local', async ({ page }) => {
  await openSource(page, 99)
  await page.getByLabel('选择本地 PDF').setInputFiles(file)
  await expect(page.getByText(/来源页号缺失或超出/)).toBeVisible()
  await expect(page.locator('.local-pdf-canvas canvas')).toHaveCount(0)
  await expect(page.getByRole('button', { name: '回到来源页' })).toBeDisabled()
  await page.getByLabel('PDF 页码', { exact: true }).fill('1')
  await page.getByRole('button', { name: '跳转', exact: true }).click()
  await expect(page.getByRole('img', { name: '本地 PDF 第 1 页（文件身份未核验）' })).toBeVisible()
  await page.getByLabel('选择本地 PDF').setInputFiles({ name: 'invalid.pdf', mimeType: 'application/pdf', buffer: Buffer.from('not a pdf') })
  await expect(page.getByRole('alert')).toHaveText('文件不是可识别的 PDF')
  await expect(page.locator('.local-pdf-canvas canvas')).toHaveCount(0)
  await page.getByLabel('选择本地 PDF').setInputFiles(file)
  await expect(page.getByText('共 3 页 · 当前浏览 尚未选页')).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
})
