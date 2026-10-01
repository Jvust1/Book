import { afterEach, expect, it, vi } from 'vitest'
import { bookApi } from './client'
const fallback = { message: '请求失败，请稍后重试', code: null, status: 503 }
const valid = { error: { code: 'original_unavailable', message: '原创服务暂不可用' } }
function respond(body: unknown, headers: Record<string,string> = { 'content-type': 'application/json' }) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 503, headers })))
}
afterEach(() => vi.unstubAllGlobals())
it.each([
  { error: { ...valid.error, message: 'x'.repeat(1025) } },
  { error: { ...valid.error, code: 'x'.repeat(129) } },
  { error: { ...valid.error, message: ' ' } },
  { error: { ...valid.error, code: ' ' } },
  { error: { message: valid.error.message } },
  { error: { code: valid.error.code } },
  { error: { ...valid.error, internal: 'original synthetic detail' } },
  { ...valid, internal: 'original synthetic detail' },
  { error: null }, { error: [] }, null,
])('fails closed on an untrusted error envelope %#', async body => {
  respond(body)
  await expect(bookApi.getLibrary()).rejects.toMatchObject(fallback)
  expect(fetch).toHaveBeenCalledOnce()
})
it('rejects a large displayed message instead of passing it into the UI', async () => {
  respond({ error: { code: 'original', message: 'x'.repeat(3*1024*1024) } })
  const error = await bookApi.getLibrary().catch(error => error)
  expect(error.message.length).toBeLessThanOrEqual(1024)
  expect(error).toMatchObject(fallback)
})
it('rejects JSON-looking data with the wrong content type', async () => {
  respond(valid, { 'content-type': 'text/plain' })
  await expect(bookApi.getLibrary()).rejects.toMatchObject(fallback)
})
it('cancels oversized declared error bodies before consuming their payload', async () => {
  let cancelled = false
  const stream = new ReadableStream<Uint8Array>({ start(c) { c.enqueue(new TextEncoder().encode(JSON.stringify(valid))); c.close() }, cancel() { cancelled = true } })
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(stream, { status: 503,
    headers: { 'content-type': 'application/json', 'content-length': String(64*1024+1) } })))
  await expect(bookApi.getLibrary()).rejects.toMatchObject(fallback)
  expect(cancelled).toBe(true)
})
it('applies the same byte ceiling to chunked responses without Content-Length', async () => {
  let chunks = 0; let cancelled = false
  const stream = new ReadableStream<Uint8Array>({ pull(c) {
    if (chunks++ < 100) c.enqueue(new Uint8Array(4096).fill(32)); else c.close()
  }, cancel() { cancelled = true } })
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(stream, { status: 503, headers: { 'content-type': 'application/json' } })))
  await expect(bookApi.getLibrary()).rejects.toMatchObject(fallback)
  expect(chunks).toBeLessThanOrEqual(18)
  expect(cancelled).toBe(true)
})
it('rejects malformed UTF-8 rather than displaying replacement characters', async () => {
  const before = new TextEncoder().encode('{"error":{"code":"original","message":"')
  const after = new TextEncoder().encode('"}}')
  const bytes = new Uint8Array([...before, 0xc0, 0xaf, ...after])
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(bytes, { status: 503, headers: { 'content-type': 'application/json' } })))
  await expect(bookApi.getLibrary()).rejects.toMatchObject(fallback)
})
it('preserves the current bounded public error message, code and HTTP status', async () => {
  respond(valid)
  await expect(bookApi.getLibrary()).rejects.toMatchObject({ ...fallback, ...valid.error })
})
it('preserves caller cancellation during a non-2xx body read', async () => {
  const controller = new AbortController()
  const stream = new ReadableStream<Uint8Array>({ start(c) { controller.signal.addEventListener('abort', () => c.error(new DOMException('Aborted', 'AbortError'))) } })
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(stream, { status: 503, headers: { 'content-type': 'application/json' } })))
  const pending = bookApi.getSource('original', 'object', 'original', controller.signal)
  const checked = expect(pending).rejects.toMatchObject({ name: 'AbortError' })
  await Promise.resolve(); controller.abort(); await checked
  expect(fetch).toHaveBeenCalledOnce()
})
it('falls back for malformed JSON and ordinary body I/O failures without replay', async () => {
  for (const response of [new Response('{', { status: 503, headers: { 'content-type': 'application/json' } }),
    new Response(new ReadableStream({ start(c) { c.error(new TypeError('original synthetic read failure')) } }), { status: 503, headers: { 'content-type': 'application/json' } })]) {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
    await expect(bookApi.getLibrary()).rejects.toMatchObject(fallback)
    expect(fetch).toHaveBeenCalledOnce()
  }
})
it('accepts exactly bounded public error strings without rewriting them', async () => {
  const body = { error: { code: 'x'.repeat(128), message: '原'.repeat(1024) } }
  respond(body, { 'content-type': 'application/json; charset=utf-8' })
  await expect(bookApi.getLibrary()).rejects.toMatchObject({ ...fallback, ...body.error })
})
it('never automatically replays a failed mutation while rejecting its oversized error', async () => {
  respond({ error: { code: 'original', message: 'x'.repeat(1025) } })
  await expect(bookApi.completeStudy('original', 'section', 'learn')).rejects.toMatchObject(fallback)
  expect(fetch).toHaveBeenCalledOnce()
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/complete'), expect.objectContaining({ method: 'POST' }))
})
