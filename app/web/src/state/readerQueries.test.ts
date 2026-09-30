import { QueryClient, onlineManager } from '@tanstack/react-query'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, bookApi } from '../api/client'
import type { SourceResponse } from '../api/types'
import { createReaderQueryClient, readerSourceOptions, readerSearchOptions, READER_GC_MS, READER_STALE_MS, visibleReaderData } from './readerQueries'

vi.mock('../api/client', async () => ({ ...await vi.importActual<typeof import('../api/client')>('../api/client'),
  bookApi: { getSource: vi.fn(), searchCourse: vi.fn() } }))
const source = (course = 'course_a', id = 'source_1') => ({ course_id: course, book_id: 'synthetic_book',
  kind: 'object', source_id: id, content_zh: 'Original synthetic text.' }) as SourceResponse
const clients: QueryClient[] = []
const make = (gc = Infinity) => { const client = createReaderQueryClient(gc); clients.push(client); return client }
afterEach(() => { clients.splice(0).forEach(client => client.clear()); onlineManager.setOnline(true); vi.clearAllMocks(); vi.useRealTimers() })

describe('real TanStack reader cache, key isolation and cancellation', () => {
  it('deduplicates simultaneous reads and reuses a fresh validated result', async () => {
    const client = make(); let done!: (value: SourceResponse) => void
    vi.mocked(bookApi.getSource).mockReturnValue(new Promise(resolve => { done = resolve }))
    const options = readerSourceOptions('course_a', 'object', 'source_1')
    const first = client.fetchQuery(options); const second = client.fetchQuery(options)
    expect(bookApi.getSource).toHaveBeenCalledOnce()
    const value = source(); done(value)
    expect(await first).toEqual(value); expect(await second).toEqual(value)
    expect(await client.fetchQuery(options)).toEqual(value)
    expect(bookApi.getSource).toHaveBeenCalledOnce()
  })

  it('keeps courses, source kinds, queries and limits in separate keys', async () => {
    const client = make()
    vi.mocked(bookApi.getSource).mockImplementation(async (course, kind, id) => ({ ...source(course, id), kind }))
    await client.fetchQuery(readerSourceOptions('course_a', 'object', 'shared'))
    await client.fetchQuery(readerSourceOptions('course_b', 'object', 'shared'))
    await client.fetchQuery(readerSourceOptions('course_a', 'figure', 'shared'))
    expect(bookApi.getSource).toHaveBeenCalledTimes(3)
    expect(client.getQueryData(readerSourceOptions('course_a', 'object', 'shared').queryKey)?.course_id).toBe('course_a')
    expect(client.getQueryData(readerSourceOptions('course_b', 'object', 'shared').queryKey)?.course_id).toBe('course_b')
    expect(readerSearchOptions('a', 'query', 10).queryKey).not.toEqual(readerSearchOptions('a', 'query', 30).queryKey)
    expect(readerSearchOptions('a', 'query').queryKey).not.toEqual(readerSearchOptions('b', 'query').queryKey)
    expect(readerSearchOptions('a', 'query').queryKey).not.toEqual(readerSearchOptions('a', 'other').queryKey)
    expect(readerSourceOptions('a', ' OBJECT ', 'x').queryKey).toEqual(readerSourceOptions('a', 'object', 'x').queryKey)
  })

  it('consumes AbortSignal, cancels the old task and ignores its late completion', async () => {
    const client = make(); let signal!: AbortSignal; let done!: (value: SourceResponse) => void
    vi.mocked(bookApi.getSource).mockImplementationOnce((_course, _kind, _id, incoming) => {
      signal = incoming!; return new Promise(resolve => { done = resolve })
    }).mockResolvedValue(source())
    const options = readerSourceOptions('course_a', 'object', 'source_1')
    const first = client.fetchQuery(options)
    const rejected = expect(first).rejects.toThrow()
    await client.cancelQueries({ queryKey: options.queryKey, exact: true })
    await rejected
    expect(signal.aborted).toBe(true)
    done({ ...source(), content_zh: 'Old abandoned result.' }); await Promise.resolve()
    expect(client.getQueryData(options.queryKey)).toBeUndefined()
    expect(await client.fetchQuery(options)).toEqual(source())
  })

  it('cancels only the exact selected source and leaves another in-flight read alive', async () => {
    const client = make(); const signals: Record<string, AbortSignal> = {}
    const finish: Record<string, (value: SourceResponse) => void> = {}
    vi.mocked(bookApi.getSource).mockImplementation((_course, _kind, id, signal) => {
      signals[id] = signal!; return new Promise(resolve => { finish[id] = resolve })
    })
    const a = readerSourceOptions('course_a', 'object', 'a')
    const b = readerSourceOptions('course_a', 'object', 'b')
    const first = client.fetchQuery(a); const second = client.fetchQuery(b)
    const rejected = expect(first).rejects.toThrow()
    await client.cancelQueries({ queryKey: a.queryKey, exact: true }); await rejected
    expect(signals.a.aborted).toBe(true); expect(signals.b.aborted).toBe(false)
    finish.b(source('course_a', 'b'))
    expect(await second).toEqual(source('course_a', 'b'))
    expect(client.getQueryData(b.queryKey)?.source_id).toBe('b')
  })

  it('attempts local reads even if navigator online state is false, and does not automatically retry', async () => {
    onlineManager.setOnline(false)
    const client = make(); vi.mocked(bookApi.getSource).mockRejectedValue(new TypeError('network down'))
    await expect(client.fetchQuery(readerSourceOptions('a', 'object', 'x'))).rejects.toThrow('network down')
    expect(bookApi.getSource).toHaveBeenCalledOnce()
    expect(client.getDefaultOptions().mutations?.retry).toBe(false)
  })

  it('refetches stale data and garbage-collects inactive cache using upstream timers', async () => {
    vi.useFakeTimers(); const client = make(READER_GC_MS)
    vi.mocked(bookApi.getSource).mockResolvedValue(source())
    const options = readerSourceOptions('course_a', 'object', 'source_1')
    await client.fetchQuery(options)
    await vi.advanceTimersByTimeAsync(READER_STALE_MS + 1)
    await client.fetchQuery(options)
    expect(bookApi.getSource).toHaveBeenCalledTimes(2)
    await vi.advanceTimersByTimeAsync(READER_GC_MS + 1)
    expect(client.getQueryData(options.queryKey)).toBeUndefined()
  })

  it('allows labeled cached data only for network TypeErrors; API/schema failures stay closed', () => {
    const data = source()
    expect(visibleReaderData(data, null)).toBe(data)
    expect(visibleReaderData(data, new TypeError('network unavailable'))).toBe(data)
    expect(visibleReaderData(data, new ApiError('invalid', 200, 'invalid_response'))).toBeUndefined()
    expect(visibleReaderData(data, new ApiError('revoked', 403, 'forbidden'))).toBeUndefined()
    expect(visibleReaderData(data, new ApiError('gone', 404, 'source_not_found'))).toBeUndefined()
    expect(visibleReaderData(data, new ApiError('unavailable', 503, 'search_unavailable'))).toBeUndefined()
    expect(visibleReaderData(data, new Error('unknown failure'))).toBeUndefined()
    expect(visibleReaderData(undefined, new TypeError('network unavailable'))).toBeUndefined()
  })
})
