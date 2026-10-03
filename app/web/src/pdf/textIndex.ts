import type { PDFDocumentProxy } from 'pdfjs-dist'

export const MAX_SEARCH_PAGES = 50
export const MAX_PAGE_TEXT = 20_000
export const MAX_INDEX_TEXT = 250_000
export const INDEX_TIMEOUT_MS = 30_000
export interface PdfTextPage { page: number; text: string; truncated: boolean }
export interface PdfTextIndex { pages: PdfTextPage[]; start: number; requestedEnd: number; processedEnd: number; limited: boolean }

const cancelled = () => new DOMException('Cancelled', 'AbortError')
function abortable<T>(promise: Promise<T>, signal: AbortSignal): Promise<T> {
  if (signal.aborted) return Promise.reject(cancelled())
  return new Promise((resolve, reject) => {
    const abort = () => reject(cancelled())
    signal.addEventListener('abort', abort, { once: true })
    promise.then(resolve, reject).finally(() => signal.removeEventListener('abort', abort))
  })
}

/** Explicit, bounded local extraction. Cancelling stops consumption; closing the viewer destroys its PDF worker. */
export async function extractPdfText(
  pdf: Pick<PDFDocumentProxy, 'numPages' | 'getPage'>, start: number, end: number,
  signal: AbortSignal, onProgress: (page: number) => void = () => {},
): Promise<PdfTextIndex> {
  if (![start, end].every(Number.isInteger) || start < 1 || end < start || end > pdf.numPages || end - start + 1 > MAX_SEARCH_PAGES) {
    throw new Error('请选择文件内连续的 1 至 50 页')
  }
  const controller = new AbortController()
  const abort = () => controller.abort()
  signal.addEventListener('abort', abort, { once: true })
  if (signal.aborted) controller.abort()
  let timedOut = false
  const timer = setTimeout(() => { timedOut = true; controller.abort() }, INDEX_TIMEOUT_MS)
  const pages: PdfTextPage[] = []
  let total = 0
  try {
    for (let pageNumber = start; pageNumber <= end && total < MAX_INDEX_TEXT; pageNumber++) {
      if (controller.signal.aborted) throw cancelled()
      const page = await abortable(pdf.getPage(pageNumber), controller.signal)
      if (controller.signal.aborted) throw cancelled()
      const reader = page.streamTextContent().getReader()
      const stopReader = () => { void reader.cancel().catch(() => {}) }
      controller.signal.addEventListener('abort', stopReader, { once: true })
      let text = ''
      let truncated = false
      const budget = Math.min(MAX_PAGE_TEXT, MAX_INDEX_TEXT - total)
      try {
        while (true) {
          const chunk = await abortable(reader.read(), controller.signal)
          if (controller.signal.aborted) throw cancelled()
          if (chunk.done) break
          for (const item of chunk.value.items ?? []) {
            if (!('str' in item) || typeof item.str !== 'string' || !item.str) continue
            const fragment = (text ? ' ' : '') + item.str
            const remaining = budget - text.length
            text += fragment.slice(0, remaining)
            if (fragment.length >= remaining) { truncated = true; break }
          }
          if (truncated) break
        }
      } finally {
        controller.signal.removeEventListener('abort', stopReader)
        // No page.cleanup(): this page can be concurrently displayed by the viewer.
        void reader.cancel().catch(() => {})
        reader.releaseLock()
      }
      if (controller.signal.aborted) throw cancelled()
      pages.push({ page: pageNumber, text, truncated })
      total += text.length
      onProgress(pageNumber)
    }
    const processedEnd = pages.at(-1)?.page ?? start - 1
    return { pages, start, requestedEnd: end, processedEnd,
      limited: processedEnd < end || pages.some(page => page.truncated) }
  } catch (error) {
    if (timedOut) throw new Error('提取已超过 30 秒，请缩小页码范围后重试')
    if (controller.signal.aborted) throw cancelled()
    throw error
  } finally {
    clearTimeout(timer)
    signal.removeEventListener('abort', abort)
  }
}
