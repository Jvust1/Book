import { Buffer } from 'node:buffer'
import { expect, test, type Locator, type Page, type Route } from '@playwright/test'
import { syntheticPdf } from './syntheticPdf'

// Original, deterministic text with a unique search term on each physical page.
// Indexing pages 2–3 must retain page 3's identity rather than its array position.
const pageTexts = [
  'Marigold meadow on physical page one.',
  'Origami compass on physical page two.',
  'Quartz resonance on physical page three.',
] as const
const file = {
  name: 'original-search-fixture.pdf', mimeType: 'application/pdf',
  buffer: Buffer.from(syntheticPdf(pageTexts.length, pageTexts)),
}
const sourcePath = '/courses/synthetic_search/sources/object/synthetic_source'
const sourceApiPath = `/api${sourcePath}`

function isFuseWorkerScript(url: URL) {
  // ?url is Vite's module wrapper, not the actual worker request. Production
  // emits fuse.worker-<hash>.mjs from upstream's fuse.js/worker-script export.
  return !url.searchParams.has('url') &&
    /\/(?:assets\/fuse\.worker-[^/]+\.mjs|node_modules\/fuse\.js\/dist\/fuse\.worker\.mjs)$/.test(url.pathname)
}

async function openSource(page: Page) {
  await page.route(`**${sourceApiPath}`, route => route.fulfill({ json: {
    course_id: 'synthetic_search', book_id: 'synthetic_book', section_id: 'synthetic_s01',
    kind: 'object', source_id: 'synthetic_source', type: 'formula', type_zh: '公式', number: '1',
    title_zh: '原创本地查找验收', title_en: null, content_zh: '仅用于工程验收的原创结构化说明。',
    formula: 'x^2=9', printed_page: 17, pdf_page: 2, source_anchor: 'synthetic:source-2',
    source_batch: 'synthetic-test-only', translation_available: true, context_before: [], context_after: [],
  } }))
  await page.goto(sourcePath)
  await expect(page.getByRole('heading', { name: '对照本地 PDF' })).toBeVisible()
}

async function selectPdf(page: Page) {
  await page.getByLabel('选择本地 PDF').setInputFiles(file)
  await expect(page.getByRole('img', { name: '本地 PDF 第 2 页（文件身份未核验）' })).toBeVisible()
  await expect(page.getByText('正在显示 PDF 页…', { exact: true })).toHaveCount(0)
  const search = page.getByRole('region', { name: '本地 PDF 文本查找' })
  await expect(search).toBeVisible()
  return search
}

async function extractRange(search: Locator, start: number, end: number) {
  await search.getByLabel('提取起始页', { exact: true }).fill(String(start))
  await search.getByLabel('提取结束页', { exact: true }).fill(String(end))
  await search.getByRole('button', { name: '提取所选页文本', exact: true }).click()
  await expect(search.getByText(`已提取 PDF 第 ${start} 至 ${end} 页 · 共 ${end - start + 1} 页有文本`, { exact: true })).toBeVisible()
}

async function query(search: Locator, text: string) {
  await search.getByRole('textbox', { name: '本地查找词', exact: true }).fill(text)
  await search.getByRole('button', { name: '查找所选页', exact: true }).click()
}

async function expectOneHit(search: Locator, page: number) {
  await expect(search.getByText('近似匹配 1 页（最多 10 页） · fuse.js@7.5.0', { exact: true })).toBeVisible()
  await expect(search.locator('.pdf-search-results li')).toHaveCount(1)
  await expect(search.getByRole('button', { name: `浏览本地 PDF 第 ${page} 页`, exact: true })).toBeVisible()
  await expect(search.locator('.pdf-search-results p')).toHaveText(pageTexts[page - 1])
  expect(await search.locator('.pdf-search-results mark').count()).toBeGreaterThan(0)
  await expect(search.getByRole('link')).toHaveCount(0)
}

async function browserStorage(page: Page) {
  return page.evaluate(async () => ({
    local: JSON.stringify(localStorage), session: JSON.stringify(sessionStorage),
    databases: (await indexedDB.databases()).map(({ name, version }) => ({ name, version })),
  }))
}

for (const viewport of [{ name: 'desktop', width: 1280, height: 900 }, { name: 'narrow', width: 390, height: 844 }]) {
  test(`real local PDF text extraction and fuzzy physical-page navigation (${viewport.name})`, async ({ page, context, baseURL }) => {
    await page.setViewportSize(viewport)
    const unexpectedRequests: string[] = []
    const errors: string[] = []
    const workers: string[] = []
    context.on('request', request => {
      const url = new URL(request.url())
      if (request.method() !== 'GET' || url.origin !== new URL(baseURL!).origin ||
        (url.pathname.startsWith('/api/') && url.pathname !== sourceApiPath)) {
        unexpectedRequests.push(`${request.method()} ${request.url()}`)
      }
    })
    page.on('pageerror', error => errors.push(error.message))
    page.on('worker', worker => workers.push(worker.url()))
    await openSource(page)
    const storageBefore = await browserStorage(page)
    const canonicalFacts = page.getByLabel('教材来源定位', { exact: true })
    const factsBefore = await canonicalFacts.innerText()
    const search = await selectPdf(page)

    // Selecting the PDF alone must not silently build a searchable index.
    await expect(search.getByRole('textbox', { name: '本地查找词', exact: true })).toHaveCount(0)
    await expect(search.getByText(/已提取 PDF 第/)).toHaveCount(0)
    await expect(search.getByText(/文件身份仍未核验；匹配结果不是教材引用或答案/)).toBeVisible()
    await extractRange(search, 2, 3)
    await expect(search.getByRole('button', { name: '查找所选页', exact: true })).toBeDisabled()

    // This misspelling never occurs in the original PDF: an exact-only or mocked
    // search cannot pass. The upstream FuseWorker script must actually start.
    await query(search, 'resonanse')
    await expectOneHit(search, 3)
    expect(workers.some(url => isFuseWorkerScript(new URL(url)))).toBe(true)
    await search.getByRole('button', { name: '浏览本地 PDF 第 3 页', exact: true }).click()
    await expect(page.getByRole('img', { name: '本地 PDF 第 3 页（文件身份未核验）' })).toBeVisible()
    await expect(page.getByText('正在显示 PDF 页…', { exact: true })).toHaveCount(0)
    await page.getByText('本页可提取文本（辅助，最多 50,000 字符）', { exact: true }).click()
    await expect(page.locator('.pdf-text p')).toHaveText(pageTexts[2])
    await expect(page.getByLabel('PDF 页码', { exact: true })).toHaveValue('3')
    await expect(page.getByText('当前浏览页不是教材标注的来源页。', { exact: true })).toBeVisible()
    await expect(page.getByText(/本地文件：original-search-fixture.pdf。尚未核验/)).toBeVisible()
    await expect(canonicalFacts).toHaveText(factsBefore, { useInnerText: true })
    await expect(canonicalFacts.getByText('PDF 页：2', { exact: true })).toBeVisible()
    await expect(canonicalFacts.getByText('教材页：17', { exact: true })).toBeVisible()
    await expect(page).toHaveURL(new URL(sourcePath, baseURL).href)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth && document.body.scrollWidth <= innerWidth)).toBe(true)
    expect(await browserStorage(page)).toEqual(storageBefore)
    // Body overflow alone misses a child extending into a card's padding.
    expect(await search.evaluate(element => {
      const parent = element.parentElement!
      const box = parent.getBoundingClientRect()
      const style = getComputedStyle(parent)
      const child = element.getBoundingClientRect()
      return child.left >= box.left + parseFloat(style.paddingLeft) &&
        child.right <= box.right - parseFloat(style.paddingRight) + 1
    })).toBe(true)
    await page.screenshot({ path: `test-results/fuse-local-pdf-pilot-${viewport.name}.png`, fullPage: true })

    await page.getByRole('button', { name: '关闭本地 PDF', exact: true }).click()
    await expect(search).toHaveCount(0)
    await expect(page.locator('.local-pdf-canvas canvas')).toHaveCount(0)
    await selectPdf(page)
    await expect(search.getByRole('textbox', { name: '本地查找词', exact: true })).toHaveCount(0)
    await expect(search.getByText(/已提取 PDF 第|近似匹配/)).toHaveCount(0)
    await expect(search.getByLabel('提取起始页', { exact: true })).toHaveValue('1')
    await expect(search.getByLabel('提取结束页', { exact: true })).toHaveValue('3')
    await extractRange(search, 1, 1)
    await expect(search.getByRole('textbox', { name: '本地查找词', exact: true })).toHaveValue('')
    await query(search, 'marigold')
    await expectOneHit(search, 1)
    await expect(search.getByRole('button', { name: '浏览本地 PDF 第 3 页', exact: true })).toHaveCount(0)
    await search.getByRole('button', { name: '清空本地索引', exact: true }).click()
    await expect(search.getByRole('textbox', { name: '本地查找词', exact: true })).toHaveCount(0)
    await expect(search.getByText(/已提取 PDF 第|近似匹配/)).toHaveCount(0)
    await page.reload()
    await expect(page.getByRole('heading', { name: '对照本地 PDF' })).toBeVisible()
    await expect(search).toHaveCount(0)
    await expect(page.locator('.local-pdf-canvas canvas')).toHaveCount(0)
    expect(await browserStorage(page)).toEqual(storageBefore)
    expect(unexpectedRequests).toEqual([])
    expect(errors).toEqual([])
  })
}

test('invalid ranges and no-match results are explicit and recoverable within selected pages', async ({ page }) => {
  await openSource(page)
  const search = await selectPdf(page)
  for (const [start, end] of [['3', '2'], ['0', '2'], ['1', '4'], ['1.5', '2']]) {
    await search.getByLabel('提取起始页', { exact: true }).fill(start)
    await search.getByLabel('提取结束页', { exact: true }).fill(end)
    await search.getByRole('button', { name: '提取所选页文本', exact: true }).click()
    await expect(search.getByRole('status')).toHaveText('请选择文件内连续的 1 至 50 页')
    await expect(search.getByRole('textbox', { name: '本地查找词', exact: true })).toHaveCount(0)
    await expect(search.getByRole('button', { name: '提取所选页文本', exact: true })).toBeEnabled()
  }
  await extractRange(search, 2, 3)
  await expect(search.getByRole('status')).toHaveCount(0)
  await query(search, 'marigold')
  await expect(search.getByText('近似匹配 0 页（最多 10 页） · fuse.js@7.5.0', { exact: true })).toBeVisible()
  await expect(search.getByText('已提取范围内未找到匹配；这不表示全书没有相关内容。', { exact: true })).toBeVisible()
  await expect(search.locator('.pdf-search-results li')).toHaveCount(0)
  await expect(page.getByLabel('PDF 页码', { exact: true })).toHaveValue('2')

  // A fresh in-range query works, then expanding the range finds page 1's text.
  await query(search, 'resonanse')
  await expectOneHit(search, 3)
  await expect(search.getByText(/已提取范围内未找到匹配/)).toHaveCount(0)
  await extractRange(search, 1, 3)
  await expect(search.locator('.pdf-search-results li')).toHaveCount(0)
  await query(search, 'marigold')
  await expectOneHit(search, 1)
  await search.getByRole('button', { name: '浏览本地 PDF 第 1 页', exact: true }).click()
  await expect(page.getByRole('img', { name: '本地 PDF 第 1 页（文件身份未核验）' })).toBeVisible()
  await expect(page.getByLabel('PDF 页码', { exact: true })).toHaveValue('1')
})

test.describe('interrupted Fuse worker network', () => {
  // Only the deliberate network-interception test disables the production PWA.
  test.use({ serviceWorkers: 'block' })

  test('cancels pending worker startup and recovers using a fresh real Fuse worker', async ({ page, context }) => {
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    let release!: () => void
    const gate = new Promise<void>(resolve => { release = resolve })
    const heldRequests: string[] = []
    const holdWorker = async (route: Route) => {
      heldRequests.push(route.request().url())
      await gate
      try { await route.continue() } catch { /* Termination can abandon the held fetch. */ }
    }
    await context.route(isFuseWorkerScript, holdWorker)
    try {
      await openSource(page)
      const search = await selectPdf(page)
      await extractRange(search, 2, 3)
      await query(search, 'resonanse')
      // Do not cancel until the real script request has reached the interception.
      await expect.poll(() => heldRequests.length).toBe(1)
      await expect(search.getByRole('status')).toHaveText('正在本机匹配文本…')
      await search.getByRole('button', { name: '取消本地查找', exact: true }).click()
      await expect(search.getByRole('status')).toHaveText('已取消，未保留未完成的结果')
      await expect(search.getByRole('textbox', { name: '本地查找词', exact: true })).toHaveValue('resonanse')
      await expect(search.getByRole('button', { name: '查找所选页', exact: true })).toBeEnabled()
      await expect(search.locator('.pdf-search-results li')).toHaveCount(0)
      release()
      await context.unroute(isFuseWorkerScript, holdWorker)

      const freshWorker = page.waitForEvent('worker', { predicate: worker => isFuseWorkerScript(new URL(worker.url())) })
      await query(search, 'origami')
      await freshWorker
      await expectOneHit(search, 2)
      await expect(search.getByRole('status')).toHaveCount(0)
      await expect(search.getByRole('button', { name: '浏览本地 PDF 第 3 页', exact: true })).toHaveCount(0)
      await search.getByRole('button', { name: '浏览本地 PDF 第 2 页', exact: true }).click()
      await expect(page.getByRole('img', { name: '本地 PDF 第 2 页（文件身份未核验）' })).toBeVisible()
      expect(errors).toEqual([])
    } finally {
      release()
      await context.unroute(isFuseWorkerScript, holdWorker)
    }
  })
})
