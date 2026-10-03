import type { PDFDocumentProxy } from 'pdfjs-dist'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { extractPdfText, INDEX_TIMEOUT_MS, MAX_INDEX_TEXT, MAX_PAGE_TEXT } from './textIndex'

const streamPage = (items: unknown[]) => ({ streamTextContent: () => new ReadableStream({
  start(controller) { controller.enqueue({ items }); controller.close() },
}) })
function documentFor(texts: string[]) {
  return { numPages: texts.length, getPage: vi.fn(async (page: number) => streamPage([{ str: texts[page - 1] }])) } as unknown as Pick<PDFDocumentProxy, 'numPages' | 'getPage'>
}
afterEach(() => vi.useRealTimers())

describe('bounded local PDF text extraction', () => {
  it('extracts selected physical pages only and preserves original text', async () => {
    const pdf = documentFor(['outside', '原创 topology <script>text</script>', 'geometry'])
    const progress = vi.fn()
    const index = await extractPdfText(pdf, 2, 3, new AbortController().signal, progress)
    expect(index).toEqual({ pages: [{ page: 2, text: '原创 topology <script>text</script>', truncated: false },
      { page: 3, text: 'geometry', truncated: false }], start: 2, requestedEnd: 3, processedEnd: 3, limited: false })
    expect(pdf.getPage).not.toHaveBeenCalledWith(1)
    expect(progress.mock.calls).toEqual([[2], [3]])
  })

  it.each([[0, 1], [1, 0], [1, 51], [1.5, 2], [NaN, 2], [1, 101]])('rejects invalid or oversized range %s to %s', async (start, end) => {
    const pdf = documentFor(Array(100).fill('text'))
    await expect(extractPdfText(pdf, start, end, new AbortController().signal)).rejects.toThrow('1 至 50')
    expect(pdf.getPage).not.toHaveBeenCalled()
  })

  it('reports per-page and total character truncation without claiming the whole range', async () => {
    const pdf = documentFor(Array(50).fill('x'.repeat(MAX_PAGE_TEXT + 1)))
    const index = await extractPdfText(pdf, 1, 50, new AbortController().signal)
    expect(index.pages.reduce((n, page) => n + page.text.length, 0)).toBe(MAX_INDEX_TEXT)
    expect(index.pages.every(page => page.truncated)).toBe(true)
    expect(index.processedEnd).toBe(13)
    expect(index.requestedEnd).toBe(50)
    expect(index.limited).toBe(true)
    expect(pdf.getPage).toHaveBeenCalledTimes(13)
  })

  it('preserves empty/scanned pages as explicitly empty entries', async () => {
    const result = await extractPdfText(documentFor(['', 'visible']), 1, 2, new AbortController().signal)
    expect(result.pages[0]).toEqual({ page: 1, text: '', truncated: false })
    expect(result.limited).toBe(false)
  })

  it('does not start extraction when already aborted', async () => {
    const pdf = documentFor(['text']); const controller = new AbortController(); controller.abort()
    await expect(extractPdfText(pdf, 1, 1, controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
    expect(pdf.getPage).not.toHaveBeenCalled()
  })

  it('cancels an active text stream and discards partial results', async () => {
    const cancel = vi.fn()
    const started = vi.fn()
    const controller = new AbortController()
    const pdf = { numPages: 1, getPage: vi.fn(async () => ({ streamTextContent: () => new ReadableStream({ start: started, cancel }) })) } as unknown as PDFDocumentProxy
    const result = extractPdfText(pdf, 1, 1, controller.signal)
    const assertion = expect(result).rejects.toMatchObject({ name: 'AbortError' })
    await vi.waitFor(() => expect(started).toHaveBeenCalledOnce())
    controller.abort()
    await assertion
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('times out a stalled page without destroying the shared viewer document', async () => {
    vi.useFakeTimers()
    const destroy = vi.fn()
    const pdf = { numPages: 1, getPage: () => new Promise(() => {}), destroy } as unknown as PDFDocumentProxy
    const assertion = expect(extractPdfText(pdf, 1, 1, new AbortController().signal)).rejects.toThrow('30 秒')
    await vi.advanceTimersByTimeAsync(INDEX_TIMEOUT_MS)
    await assertion
    expect(destroy).not.toHaveBeenCalled()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('ignores a page that arrives after cancellation', async () => {
    let finish!: (page: unknown) => void
    const page = { streamTextContent: vi.fn() }
    const pdf = { numPages: 1, getPage: () => new Promise(resolve => { finish = resolve }) } as unknown as PDFDocumentProxy
    const controller = new AbortController()
    const assertion = expect(extractPdfText(pdf, 1, 1, controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
    controller.abort(); await assertion; finish(page); await Promise.resolve()
    expect(page.streamTextContent).not.toHaveBeenCalled()
  })
})
