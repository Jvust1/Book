import { afterEach, describe, expect, it, vi } from 'vitest'
import { boundedCanvasScale, loadLocalPdf, MAX_CANVAS_PIXELS, MAX_PDF_BYTES, sourcePageInRange } from './localPdf'

const state = vi.hoisted(() => ({ getDocument: vi.fn(), GlobalWorkerOptions: { workerSrc: '' } }))
vi.mock('pdfjs-dist', () => state)
afterEach(() => { vi.clearAllMocks() })
const fakeFile = (bytes: string, size = bytes.length) => ({ size, arrayBuffer: async () => new TextEncoder().encode(bytes).buffer }) as File

describe('local PDF loading boundary', () => {
  it('passes only local bytes and same-origin rendering assets to real PDF.js API shape', async () => {
    const document = { numPages: 2 }
    const destroy = vi.fn().mockResolvedValue(undefined)
    state.getDocument.mockReturnValue({ promise: Promise.resolve(document), destroy })
    const loaded = await loadLocalPdf(fakeFile('%PDF-1.7 synthetic'), new AbortController().signal)
    expect(loaded.document).toBe(document)
    const options = state.getDocument.mock.calls[0][0]
    expect(options.data).toBeInstanceOf(Uint8Array)
    expect(options).not.toHaveProperty('url')
    expect(options).not.toHaveProperty('password')
    expect(options).not.toHaveProperty('httpHeaders')
    expect(options.enableXfa).toBe(false)
    expect(options.stopAtErrors).toBe(true)
    expect(new URL(options.cMapUrl).origin).toBe(window.location.origin)
    await loaded.dispose(); await loaded.dispose()
    expect(destroy).toHaveBeenCalledTimes(1)
  })

  it.each([0, MAX_PDF_BYTES + 1])('rejects file size %s before loading a worker', async size => {
    await expect(loadLocalPdf(fakeFile('%PDF-', size), new AbortController().signal)).rejects.toThrow('100 MiB')
    expect(state.getDocument).not.toHaveBeenCalled()
  })

  it('rejects non-PDF bytes regardless of extension and handles early cancellation', async () => {
    await expect(loadLocalPdf(fakeFile('<html>'), new AbortController().signal)).rejects.toThrow('不是可识别的 PDF')
    const controller = new AbortController(); controller.abort()
    await expect(loadLocalPdf(fakeFile('%PDF-'), controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
    expect(state.getDocument).not.toHaveBeenCalled()
  })

  it('destroys rejected documents without exposing parser internals', async () => {
    const destroy = vi.fn().mockResolvedValue(undefined)
    state.getDocument.mockReturnValue({ promise: Promise.reject(new Error('internal private path')), destroy })
    await expect(loadLocalPdf(fakeFile('%PDF-'), new AbortController().signal)).rejects.toThrow('PDF 无法读取，请检查文件是否完整')
    expect(destroy).toHaveBeenCalledOnce()
  })

  it('cancels an in-flight loader and releases it once', async () => {
    let reject!: (reason: unknown) => void
    const promise = new Promise((_resolve, rejectPromise) => { reject = rejectPromise })
    const destroy = vi.fn().mockImplementation(async () => { reject(new Error('destroyed')) })
    state.getDocument.mockReturnValue({ promise, destroy })
    const controller = new AbortController()
    const loading = loadLocalPdf(fakeFile('%PDF-'), controller.signal)
    await vi.waitFor(() => expect(state.getDocument).toHaveBeenCalledOnce())
    controller.abort()
    await expect(loading).rejects.toMatchObject({ name: 'AbortError' })
    expect(destroy).toHaveBeenCalledOnce()
  })
})

describe('source location and canvas budgets', () => {
  it.each([null, 0, -1, 1.5, NaN, Infinity, 4])('does not relabel invalid source page %s as a valid page', page => {
    expect(sourcePageInRange(page, 3)).toBe(false)
  })
  it('accepts only 1-based source pages within the actual PDF', () => {
    expect(sourcePageInRange(1, 3)).toBe(true)
    expect(sourcePageInRange(3, 3)).toBe(true)
  })
  it('bounds high-DPI and hostile page dimensions', () => {
    for (const [width, height, requested] of [[600, 800, 2], [100_000, 200_000, 4], [1e9, 1, 2]]) {
      const scale = boundedCanvasScale(width, height, requested)
      expect(width * height * scale ** 2).toBeLessThanOrEqual(MAX_CANVAS_PIXELS + 1)
      expect(Math.max(width, height) * scale).toBeLessThanOrEqual(8192)
    }
    expect(() => boundedCanvasScale(Infinity, 10, 1)).toThrow()
    expect(() => boundedCanvasScale(0, 10, 1)).toThrow()
  })
})
