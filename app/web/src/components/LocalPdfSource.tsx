import { useEffect, useRef, useState } from 'react'
import type { PDFDocumentProxy, RenderTask } from 'pdfjs-dist'
import { boundedCanvasScale, loadLocalPdf, sourcePageInRange, type LoadedLocalPdf } from '../pdf/localPdf'

interface LocalPdfSourceProps {
  bookId: string
  sourceId: string
  sourcePage: number | null
}

export function LocalPdfSource({ bookId, sourceId, sourcePage }: LocalPdfSourceProps) {
  const [file, setFile] = useState<File | null>(null)
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null)
  const [pageNumber, setPageNumber] = useState<number | null>(null)
  const [pageInput, setPageInput] = useState('1')
  const [zoom, setZoom] = useState(1)
  const [loading, setLoading] = useState(false)
  const [rendering, setRendering] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pageText, setPageText] = useState('')
  const [textExpanded, setTextExpanded] = useState(false)
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!file) return
    let current: LoadedLocalPdf | null = null
    const controller = new AbortController()
    setPdf(null)
    setTextExpanded(false)
    setPageNumber(null)
    setPageText('')
    setLoading(true)
    setError(null)
    void loadLocalPdf(file, controller.signal).then(loaded => {
      current = loaded
      if (controller.signal.aborted) { void loaded.dispose(); return }
      const document = loaded.document
      setPdf(document)
      const target = sourcePageInRange(sourcePage, document.numPages) ? sourcePage : null
      setPageNumber(target)
      setPageInput(String(target ?? 1))
      setZoom(1)
      setLoading(false)
    }).catch(reason => {
      if (controller.signal.aborted) return
      setLoading(false)
      setError(reason instanceof Error ? reason.message : 'PDF 无法读取')
    })
    return () => {
      controller.abort()
      if (current) void current.dispose().catch(() => {})
    }
  }, [file, sourcePage])

  useEffect(() => {
    const host = hostRef.current
    if (!pdf || pageNumber === null || !host) return
    let active = true
    let renderTask: RenderTask | null = null
    const canvas = document.createElement('canvas')
    canvas.setAttribute('role', 'img')
    canvas.setAttribute('aria-label', `本地 PDF 第 ${pageNumber} 页（文件身份未核验）`)
    host.replaceChildren(canvas)
    setRendering(true)
    setError(null)
    setPageText('')
    void (async () => {
      const page = await pdf.getPage(pageNumber)
      if (!active) return
      const original = page.getViewport({ scale: 1 })
      const width = Math.max(240, host.clientWidth)
      const scale = Math.min(1.5, width / original.width) * zoom
      const viewport = page.getViewport({ scale })
      const pixelScale = boundedCanvasScale(viewport.width, viewport.height, Math.min(window.devicePixelRatio || 1, 2))
      canvas.width = Math.ceil(viewport.width * pixelScale)
      canvas.height = Math.ceil(viewport.height * pixelScale)
      canvas.style.width = `${viewport.width}px`
      canvas.style.height = `${viewport.height}px`
      // Canvas only: no scripting, link, attachment, form or HTML annotation layer.
      renderTask = page.render({ canvas, viewport, transform: [pixelScale, 0, 0, pixelScale, 0, 0], annotationMode: 0 })
      const [text] = await Promise.all([page.getTextContent(), renderTask.promise])
      if (!active) return
      setPageText(text.items.map(item => 'str' in item ? item.str : '').join(' ').slice(0, 50_000))
      setRendering(false)
      page.cleanup()
    })().catch(() => {
      if (!active) return
      host.replaceChildren()
      setRendering(false)
      setError('此页无法完整显示，未将其他页替代为来源页')
    })
    return () => {
      active = false
      renderTask?.cancel()
      if (canvas.parentNode === host) canvas.remove()
    }
  }, [pdf, pageNumber, zoom])

  const close = () => {
    setFile(null)
    setPdf(null)
    setTextExpanded(false)
    setPageNumber(null)
    setPageText('')
    setError(null)
    setLoading(false)
    setRendering(false)
    hostRef.current?.replaceChildren()
  }

  const goToPage = (value: number) => {
    if (!pdf || !sourcePageInRange(value, pdf.numPages)) {
      setError('页码必须是本地 PDF 范围内的整数')
      return
    }
    setPageNumber(value)
    setPageInput(String(value))
    setError(null)
  }

  return (
    <section className="local-pdf-source" aria-label="本地 PDF 来源预览">
      <h2>对照本地 PDF</h2>
      <p>选择你有权使用的 PDF，仅在当前浏览器内读取，不上传、不保存到学习记录。</p>
      <p className="secondary-text">预览不执行脚本或打开链接，不显示交互表单与批注；超大图像可能受渲染预算限制，请以完整原文件为准。</p>
      <p className="secondary-text">教材 {bookId} · 来源 {sourceId} · 来源 PDF 页 {sourcePage ?? '暂缺'}</p>
      <label className="pdf-file-label">
        选择本地 PDF
        <input type="file" accept="application/pdf,.pdf" onChange={event => {
          const selected = event.currentTarget.files?.[0]
          if (selected) setFile(selected)
          event.currentTarget.value = ''
        }} />
      </label>
      {file ? <button type="button" className="secondary-button" onClick={close}>关闭本地 PDF</button> : null}
      {file ? <p className="pdf-identity-warning">本地文件：{file.name}。尚未核验是否与该教材及版本匹配，请自行对照。</p> : null}
      {loading ? <p role="status">正在本机读取 PDF…</p> : null}
      {pdf ? <>
        <p>共 {pdf.numPages} 页 · 当前浏览 {pageNumber === null ? '尚未选页' : `第 ${pageNumber} 页`}</p>
        {!sourcePageInRange(sourcePage, pdf.numPages) ? (
          <p className="pdf-identity-warning">来源页号缺失或超出此文件范围。请手动选页；手动浏览不代表来源匹配。</p>
        ) : null}
        {pageNumber !== null && pageNumber !== sourcePage ? <p className="pdf-identity-warning">当前浏览页不是教材标注的来源页。</p> : null}
        <div className="pdf-controls">
          <button type="button" className="secondary-button" disabled={pageNumber === null || pageNumber <= 1} onClick={() => goToPage(pageNumber! - 1)}>上一页</button>
          <button type="button" className="secondary-button" disabled={pageNumber === null || pageNumber >= pdf.numPages} onClick={() => goToPage(pageNumber! + 1)}>下一页</button>
          <label>PDF 页码 <input aria-label="PDF 页码" type="number" min="1" max={pdf.numPages} value={pageInput} onChange={event => setPageInput(event.target.value)} /></label>
          <button type="button" className="secondary-button" onClick={() => goToPage(Number(pageInput))}>跳转</button>
          <button type="button" className="secondary-button" disabled={!sourcePageInRange(sourcePage, pdf.numPages)} onClick={() => goToPage(sourcePage!)}>回到来源页</button>
          <label>缩放 <select aria-label="PDF 缩放" value={zoom} onChange={event => setZoom(Number(event.target.value))}>
            <option value={0.75}>75%</option><option value={1}>适合宽度</option><option value={1.5}>150%</option><option value={2}>200%</option>
          </select></label>
        </div>
      </> : null}
      {rendering ? <p role="status">正在显示 PDF 页…</p> : null}
      {error ? <p role="alert">{error}</p> : null}
      <div className="local-pdf-canvas" ref={hostRef} />
      {pdf && pageNumber !== null && !rendering && !error ? (
        <details className="pdf-text" open={textExpanded} onToggle={event => setTextExpanded(event.currentTarget.open)}><summary>本页可提取文本（辅助，最多 50,000 字符）</summary><p>{pageText || '本页无可提取文本，可能是扫描图像。此处没有自动 OCR。'}</p></details>
      ) : null}
    </section>
  )
}
