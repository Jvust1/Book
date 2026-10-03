import Fuse from 'fuse.js'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PDF_SEARCH_OPTIONS, resultSnippets, searchPdfPages, type PageSearcher } from './fuzzySearch'
import type { PdfTextPage } from './textIndex'
const pages: PdfTextPage[] = [
  { page: 2, text: 'Algebra studies mathematical structures.', truncated: false },
  { page: 8, text: 'Synthetic geometry studies shapes and distances.', truncated: false },
  { page: 13, text: '原创 topology studies continuity.', truncated: false },
]
const actual = (docs: PdfTextPage[]) => new Fuse(docs, PDF_SEARCH_OPTIONS)
const realSearcher = (docs: PdfTextPage[]): PageSearcher => ({ search: async (query, options) => actual(docs).search(query, options), terminate: vi.fn() })
afterEach(() => vi.useRealTimers())

describe('real Fuse.js page search and verified local result projection', () => {
  it('matches a typo and returns its physical page and source-derived snippet', async () => {
    const result = await searchPdfPages(pages, 'geomtry', new AbortController().signal, realSearcher)
    expect(result).toHaveLength(1)
    expect(result[0]).toMatchObject({ page: 8, snippet: pages[1].text })
    expect(result[0].marks.length).toBeGreaterThan(0)
  })

  it('searches beyond the default location window and retains Chinese text offsets', async () => {
    const docs = [{ page: 21, text: 'x'.repeat(300) + ' 原创拓扑 continuity ', truncated: false }]
    const result = await searchPdfPages(docs, '原创拓扑', new AbortController().signal, realSearcher)
    expect(result[0].page).toBe(21)
    expect(result[0].before).toBe(true)
    expect(result[0].snippet.length).toBeLessThanOrEqual(220)
    expect(result[0].snippet.slice(...result[0].marks[0])).toBe('原创拓扑')
  })

  it('never interprets PDF text as HTML and preserves literal source text', async () => {
    const docs = [{ page: 1, text: '<img src=x onerror=alert(1)> synthetic geometry', truncated: false }]
    const [hit] = await searchPdfPages(docs, 'geometry', new AbortController().signal, realSearcher)
    expect(hit.snippet).toContain('<img src=x onerror=alert(1)>')
  })

  it('returns no match without expanding the scope beyond indexed pages', async () => {
    expect(await searchPdfPages(pages.slice(0, 1), 'geometry', new AbortController().signal, realSearcher)).toEqual([])
  })

  it.each(['a', 'x'.repeat(65), '   '])('rejects invalid query before constructing a worker: %s', async query => {
    const make = vi.fn(realSearcher)
    await expect(searchPdfPages(pages, query, new AbortController().signal, make)).rejects.toThrow('2 至 64')
    expect(make).not.toHaveBeenCalled()
  })

  it('rejects oversized or duplicate page indexes', async () => {
    await expect(searchPdfPages([pages[0], pages[0]], 'algebra', new AbortController().signal, realSearcher)).rejects.toThrow('budget')
    await expect(searchPdfPages([{ ...pages[0], text: 'a'.repeat(20001) }], 'algebra', new AbortController().signal, realSearcher)).rejects.toThrow('budget')
  })

  it('validates original page identity, text and match offsets before making a result navigable', () => {
    const [result] = actual(pages).search('geometry')
    expect(() => resultSnippets([{ ...result, item: { ...result.item, page: 99 } }], pages)).toThrow('provenance')
    expect(() => resultSnippets([{ ...result, item: { ...result.item, text: 'invented' } }], pages)).toThrow('provenance')
    expect(() => resultSnippets([{ ...result, matches: [{ key: 'text', indices: [[0, 99999]] }] }], pages)).toThrow('offsets')
    expect(() => resultSnippets([result, result], pages)).toThrow('provenance')
    expect(() => resultSnippets([{ ...result, score: NaN }], pages)).toThrow('provenance')
  })

  it('terminates the upstream worker after success or failure', async () => {
    const worker = realSearcher(pages)
    await searchPdfPages(pages, 'geometry', new AbortController().signal, () => worker)
    expect(worker.terminate).toHaveBeenCalledOnce()
    const broken = { search: vi.fn().mockRejectedValue(new Error('worker failed')), terminate: vi.fn() }
    await expect(searchPdfPages(pages, 'geometry', new AbortController().signal, () => broken)).rejects.toThrow()
    expect(broken.terminate).toHaveBeenCalledOnce()
  })

  it('aborts and times out stalled workers without late results', async () => {
    vi.useFakeTimers()
    const worker = { search: vi.fn(() => new Promise<never>(() => {})), terminate: vi.fn() }
    const controller = new AbortController()
    const assertion = expect(searchPdfPages(pages, 'geometry', controller.signal, () => worker)).rejects.toMatchObject({ name: 'AbortError' })
    controller.abort(); await assertion
    expect(worker.terminate).toHaveBeenCalledOnce()
    const timeout = expect(searchPdfPages(pages, 'geometry', new AbortController().signal, () => worker)).rejects.toThrow('5 秒')
    await vi.advanceTimersByTimeAsync(5000); await timeout
    expect(worker.terminate).toHaveBeenCalledTimes(2)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('does not spawn a worker for an empty index or pre-cancelled request', async () => {
    const make = vi.fn(realSearcher)
    expect(await searchPdfPages([], 'query', new AbortController().signal, make)).toEqual([])
    const controller = new AbortController(); controller.abort()
    await expect(searchPdfPages(pages, 'query', controller.signal, make)).rejects.toMatchObject({ name: 'AbortError' })
    expect(make).not.toHaveBeenCalled()
  })
})
