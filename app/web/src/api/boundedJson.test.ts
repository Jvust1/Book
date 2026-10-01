import { describe, expect, it, vi } from 'vitest'
import { MAX_VALIDATED_RESPONSE_BYTES, readBoundedJson } from './boundedJson'

describe('bounded UTF-8 JSON transport', () => {
  it('preserves split multibyte source text exactly', async () => {
    const value = { text: '原创😀 e\u0301 <script>inert</script>' }
    const bytes = new TextEncoder().encode(JSON.stringify(value))
    let index = 0
    const stream = new ReadableStream<Uint8Array>({ pull(controller) {
      if (index < bytes.length) controller.enqueue(bytes.slice(index, ++index))
      else controller.close()
    } })
    expect(await readBoundedJson(new Response(stream, { headers: { 'content-type': 'application/json; charset=utf-8' } }))).toEqual(value)
  })
  it('enforces actual streamed bytes even without a Content-Length header', async () => {
    const cancel = vi.fn()
    let pulls = 0
    const chunk = new Uint8Array(256 * 1024).fill(97)
    const stream = new ReadableStream<Uint8Array>({ pull(controller) { pulls++; controller.enqueue(chunk) }, cancel })
    await expect(readBoundedJson(new Response(stream, { headers: { 'content-type': 'application/json' } }))).rejects.toThrow('byte budget')
    expect(cancel).toHaveBeenCalledOnce()
    expect(pulls).toBeLessThanOrEqual(MAX_VALIDATED_RESPONSE_BYTES / chunk.byteLength + 2)
  })
  it('cancels a body whose declared size already exceeds the bound', async () => {
    const cancel = vi.fn()
    const stream = new ReadableStream<Uint8Array>({ cancel })
    await expect(readBoundedJson(new Response(stream, { headers: { 'content-type': 'application/json',
      'content-length': String(MAX_VALIDATED_RESPONSE_BYTES + 1) } }))).rejects.toThrow('byte budget')
    expect(cancel).toHaveBeenCalledOnce()
  })
  it('cancels an unexpected content type without reading its body', async () => {
    const cancel = vi.fn()
    const stream = new ReadableStream<Uint8Array>({ cancel })
    await expect(readBoundedJson(new Response(stream, { headers: { 'content-type': 'text/html' } }))).rejects.toThrow('encoding')
    expect(cancel).toHaveBeenCalledOnce()
  })

})

it.each([0, -1, 1.5, Infinity, MAX_VALIDATED_RESPONSE_BYTES + 1])('does not allow an invalid or expanded caller byte ceiling %s', async limit => {
  const cancel = vi.fn()
  const response = new Response(new ReadableStream({ cancel }), { headers: { 'content-type': 'application/json' } })
  await expect(readBoundedJson(response, limit)).rejects.toThrow('byte limit')
  expect(cancel).toHaveBeenCalledOnce()
})
