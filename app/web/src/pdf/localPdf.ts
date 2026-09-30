import type { PDFDocumentProxy } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

export const MAX_PDF_BYTES = 100 * 1024 * 1024
export const MAX_CANVAS_PIXELS = 8_000_000

export function sourcePageInRange(page: number | null, count: number): page is number {
  return page !== null && Number.isInteger(page) && page >= 1 && page <= count
}

export function boundedCanvasScale(width: number, height: number, requested: number): number {
  if (![width, height, requested].every(value => Number.isFinite(value) && value > 0)) {
    throw new Error('PDF 页面尺寸无效')
  }
  return Math.min(requested, Math.sqrt(MAX_CANVAS_PIXELS / (width * height)), 8192 / width, 8192 / height)
}

export interface LoadedLocalPdf {
  document: PDFDocumentProxy
  dispose: () => Promise<void>
}

export async function loadLocalPdf(file: File, signal: AbortSignal): Promise<LoadedLocalPdf> {
  if (file.size === 0 || file.size > MAX_PDF_BYTES) {
    throw new Error('请选择非空且不超过 100 MiB 的 PDF 文件')
  }
  const bytes = new Uint8Array(await file.arrayBuffer())
  if (signal.aborted) throw new DOMException('Cancelled', 'AbortError')
  const header = new TextDecoder().decode(bytes.subarray(0, 1024))
  if (!header.includes('%PDF-')) throw new Error('文件不是可识别的 PDF')
  // Deferred until the user chooses a file. No URL/document credentials are passed.
  const pdfjs = await import('pdfjs-dist')
  if (signal.aborted) throw new DOMException('Cancelled', 'AbortError')
  pdfjs.GlobalWorkerOptions.workerSrc = workerUrl
  const assetBase = new URL(`${import.meta.env.BASE_URL}pdfjs/`, window.location.href).href
  const task = pdfjs.getDocument({
    data: bytes,
    cMapUrl: `${assetBase}cmaps/`,
    cMapPacked: true,
    standardFontDataUrl: `${assetBase}standard_fonts/`,
    wasmUrl: `${assetBase}wasm/`,
    iccUrl: `${assetBase}iccs/`,
    enableXfa: false,
    stopAtErrors: true,
    maxImageSize: 16_000_000,
    canvasMaxAreaInBytes: MAX_CANVAS_PIXELS * 4,
  })
  let disposed: Promise<void> | undefined
  const dispose = () => (disposed ??= task.destroy())
  const abort = () => { void dispose().catch(() => {}) }
  signal.addEventListener('abort', abort, { once: true })
  try {
    const document = await task.promise
    if (signal.aborted) {
      await dispose()
      throw new DOMException('Cancelled', 'AbortError')
    }
    return { document, dispose }
  } catch (error) {
    await dispose().catch(() => {})
    if (signal.aborted) throw new DOMException('Cancelled', 'AbortError')
    if (error instanceof Error && error.name === 'PasswordException') {
      throw new Error('此 PDF 需要密码，当前本地预览暂不支持加密文件')
    }
    throw new Error('PDF 无法读取，请检查文件是否完整')
  } finally {
    signal.removeEventListener('abort', abort)
  }
}
