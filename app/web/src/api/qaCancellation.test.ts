import { afterEach, describe, expect, it, vi } from 'vitest'
import { bookApi } from './client'

const question = { question: 'Original bounded waiting question', section_id: null, history: [] }

afterEach(() => vi.unstubAllGlobals())

describe('explicit QA cancellation transport', () => {
  it('forwards only the caller signal and never replays an aborted POST before headers', async () => {
    const controller = new AbortController()
    const fetchMock = vi.fn((_path: string, init: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init.signal!.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
    }))
    vi.stubGlobal('fetch', fetchMock)
    const result = bookApi.askCourse('original_course', question, controller.signal)
    const failed = expect(result).rejects.toMatchObject({ name: 'AbortError' })
    expect(fetchMock).toHaveBeenCalledWith('/api/courses/original_course/qa', expect.objectContaining({
      method: 'POST', signal: controller.signal, body: JSON.stringify(question),
    }))
    controller.abort()
    await failed
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it.each([200, 503])('keeps cancellation during a stalled %s JSON body as AbortError', async status => {
    const controller = new AbortController()
    let reader!: ReadableStreamDefaultController<Uint8Array>
    const body = new ReadableStream<Uint8Array>({ start(value) { reader = value } })
    controller.signal.addEventListener('abort', () => reader.error(new DOMException('Aborted', 'AbortError')), { once: true })
    const fetchMock = vi.fn().mockResolvedValue(new Response(body, { status, headers: { 'content-type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)
    const result = bookApi.askCourse('original_course', question, controller.signal)
    const failed = expect(result).rejects.toMatchObject({ name: 'AbortError' })
    await Promise.resolve()
    expect(body.locked).toBe(true)
    controller.abort()
    await failed
    expect(body.locked).toBe(false)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
