import { FuseWorker } from 'fuse.js/worker'
import workerUrl from 'fuse.js/worker-script?url'
import type { FuseResult, IFuseOptions } from 'fuse.js'
import { MAX_INDEX_TEXT, MAX_PAGE_TEXT, MAX_SEARCH_PAGES, type PdfTextPage } from './textIndex'

export const PDF_SEARCH_ENGINE = 'fuse.js@7.5.0'
export const PDF_SEARCH_OPTIONS: IFuseOptions<PdfTextPage> = {
  keys: ['text'], threshold: 0.3, ignoreLocation: true, ignoreFieldNorm: true,
  includeMatches: true, includeScore: true, minMatchCharLength: 2, useExtendedSearch: false,
}
export interface PdfSearchHit { page: number; snippet: string; before: boolean; after: boolean; marks: [number, number][] }
export interface PageSearcher {
  search: (query: string, options: { limit: number }) => Promise<FuseResult<PdfTextPage>[]>
  terminate: () => void
}

export function resultSnippets(results: FuseResult<PdfTextPage>[], pages: PdfTextPage[]): PdfSearchHit[] {
  if (!Array.isArray(results) || results.length > 10) throw new Error('invalid search result')
  const seen = new Set<number>()
  return results.map(result => {
    const original = pages[result.refIndex]
    if (!Number.isInteger(result.refIndex) || !original || seen.has(original.page) ||
      result.item.page !== original.page || result.item.text !== original.text ||
      typeof result.score !== 'number' || !Number.isFinite(result.score) || result.score < 0 || result.score > 1) {
      throw new Error('invalid page provenance')
    }
    seen.add(original.page)
    const ranges = result.matches?.find(match => match.key === 'text')?.indices ?? []
    if (!ranges.length || ranges.some(([a, b]) => !Number.isInteger(a) || !Number.isInteger(b) || a < 0 || b < a || b >= original.text.length)) {
      throw new Error('invalid match offsets')
    }
    const start = Math.max(0, ranges[0][0] - 70)
    const end = Math.min(original.text.length, start + 220)
    const marks = ranges.slice(0, 128).filter(([a, b]) => a < end && b >= start)
      .map(([a, b]) => [Math.max(a, start) - start, Math.min(b + 1, end) - start] as [number, number])
      .sort((a, b) => a[0] - b[0])
    return { page: original.page, snippet: original.text.slice(start, end), before: start > 0, after: end < original.text.length, marks }
  })
}

/** Uses the upstream worker implementation directly; no CDN, storage, server request or custom search engine. */
export async function searchPdfPages(pages: PdfTextPage[], query: string, signal: AbortSignal,
  makeSearcher: (pages: PdfTextPage[]) => PageSearcher = docs => new FuseWorker(docs, PDF_SEARCH_OPTIONS, { numWorkers: 1, workerUrl }),
): Promise<PdfSearchHit[]> {
  const text = query.trim()
  if (text.length < 2 || text.length > 64) throw new Error('请输入 2 至 64 个字符')
  if (pages.length > MAX_SEARCH_PAGES || new Set(pages.map(page => page.page)).size !== pages.length ||
    pages.some(page => !Number.isInteger(page.page) || page.page < 1 || typeof page.text !== 'string' || page.text.length > MAX_PAGE_TEXT) ||
    pages.reduce((sum, page) => sum + page.text.length, 0) > MAX_INDEX_TEXT) throw new Error('invalid index budget')
  if (signal.aborted) throw new DOMException('Cancelled', 'AbortError')
  if (!pages.some(page => page.text.trim())) return []
  const searcher = makeSearcher(pages)
  let abort = () => {}
  let timer: ReturnType<typeof setTimeout> | undefined
  try {
    const stop = new Promise<never>((_, reject) => {
      abort = () => reject(new DOMException('Cancelled', 'AbortError'))
      signal.addEventListener('abort', abort, { once: true })
      timer = setTimeout(() => reject(new Error('搜索超过 5 秒，请缩小页码范围后重试')), 5000)
    })
    const results = await Promise.race([searcher.search(text, { limit: 10 }), stop])
    if (signal.aborted) throw new DOMException('Cancelled', 'AbortError')
    return resultSnippets(results, pages)
  } finally {
    clearTimeout(timer)
    signal.removeEventListener('abort', abort)
    searcher.terminate()
  }
}
