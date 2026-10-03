import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import { extractPdfText, type PdfTextIndex } from '../pdf/textIndex'
import { PDF_SEARCH_ENGINE, searchPdfPages, type PdfSearchHit } from '../pdf/fuzzySearch'

function Snippet({ hit }: { hit: PdfSearchHit }) {
  const parts = []
  let cursor = 0
  for (const [start, end] of hit.marks) {
    if (start < cursor || end <= start) continue
    parts.push(hit.snippet.slice(cursor, start), <mark key={`${start}:${end}`}>{hit.snippet.slice(start, end)}</mark>)
    cursor = end
  }
  parts.push(hit.snippet.slice(cursor))
  return <p>{hit.before ? '…' : ''}{parts}{hit.after ? '…' : ''}</p>
}

export function LocalPdfSearch({ pdf, onNavigate }: { pdf: PDFDocumentProxy; onNavigate: (page: number) => void }) {
  const [start, setStart] = useState('1')
  const [end, setEnd] = useState(String(Math.min(pdf.numPages, 20)))
  const [index, setIndex] = useState<PdfTextIndex | null>(null)
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<PdfSearchHit[] | null>(null)
  const [busy, setBusy] = useState<'extract' | 'search' | null>(null)
  const [progress, setProgress] = useState<number | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const active = useRef<AbortController | null>(null)
  useEffect(() => () => { active.current?.abort(); active.current = null }, [])

  const cancel = () => {
    active.current?.abort(); active.current = null
    setBusy(null); setMessage('已取消，未保留未完成的结果')
  }
  const clear = () => {
    active.current?.abort(); active.current = null
    setBusy(null); setIndex(null); setHits(null); setQuery(''); setProgress(null); setMessage(null)
  }
  const build = async () => {
    if (active.current) return
    const controller = new AbortController(); active.current = controller
    setBusy('extract'); setIndex(null); setHits(null); setProgress(null); setMessage(null)
    try {
      const next = await extractPdfText(pdf, Number(start), Number(end), controller.signal, page => {
        if (active.current === controller) setProgress(page)
      })
      if (active.current === controller) setIndex(next)
    } catch (error) {
      if (active.current === controller) setMessage(error instanceof Error && error.name !== 'AbortError' ? error.message : '提取已取消')
    } finally {
      if (active.current === controller) { active.current = null; setBusy(null) }
    }
  }
  const search = async (event: FormEvent) => {
    event.preventDefault()
    if (!index || active.current) return
    const controller = new AbortController(); active.current = controller
    setBusy('search'); setHits(null); setMessage(null)
    try {
      const next = await searchPdfPages(index.pages, query, controller.signal)
      if (active.current === controller) setHits(next)
    } catch (error) {
      if (active.current === controller) setMessage(error instanceof Error ? error.message : '搜索暂不可用，请重试')
    } finally {
      if (active.current === controller) { active.current = null; setBusy(null) }
    }
  }
  return <section className="local-pdf-search" aria-label="本地 PDF 文本查找">
    <h3>查找本地 PDF 文本</h3>
    <p>先选择最多 50 页并提取文本，再进行近似文字匹配。仅保存在当前页面内存，关闭文件即清空。</p>
    <p className="secondary-text">文件身份仍未核验；匹配结果不是教材引用或答案。扫描图像没有 OCR，公式与阅读顺序可能提取不完整。</p>
    <div className="pdf-controls">
      <label>提取起始页 <input aria-label="提取起始页" type="number" min="1" max={pdf.numPages} value={start} disabled={!!busy} onChange={event => { setStart(event.target.value); setIndex(null); setHits(null); setMessage(null) }} /></label>
      <label>提取结束页 <input aria-label="提取结束页" type="number" min="1" max={pdf.numPages} value={end} disabled={!!busy} onChange={event => { setEnd(event.target.value); setIndex(null); setHits(null); setMessage(null) }} /></label>
      <button type="button" className="secondary-button" disabled={!!busy} onClick={() => { void build() }}>提取所选页文本</button>
      {busy ? <button type="button" className="secondary-button" onClick={cancel}>取消本地查找</button> : null}
      <button type="button" className="secondary-button" onClick={clear}>清空本地索引</button>
    </div>
    {busy === 'extract' ? <p role="status">正在提取本地文本{progress === null ? '…' : `，已到第 ${progress} 页…`}</p> : null}
    {index ? <>
      <p>已提取 PDF 第 {index.start} 至 {index.processedEnd} 页 · 共 {index.pages.filter(page => page.text.trim()).length} 页有文本</p>
      <p className="secondary-text">每页最多 20,000 字符，总计最多 250,000 字符；只搜索已提取的文本。</p>
      {index.limited ? <p className="pdf-identity-warning">提取达到字符上限，部分文本或后续页未纳入。请缩小页码范围后重新提取。</p> : null}
      {!index.pages.some(page => page.text.trim()) ? <p>所选页没有可提取文本，可能是扫描图像。此处不做 OCR。</p> : <form onSubmit={event => { void search(event) }} className="pdf-search-form">
        <label htmlFor="local-pdf-query">本地查找词</label>
        <input id="local-pdf-query" value={query} minLength={2} maxLength={64} disabled={!!busy} onChange={event => { setQuery(event.target.value); setHits(null) }} />
        <button type="submit" className="secondary-button" disabled={!!busy || query.trim().length < 2}>查找所选页</button>
      </form>}
    </> : null}
    {busy === 'search' ? <p role="status">正在本机匹配文本…</p> : null}
    {message ? <p role="status">{message}</p> : null}
    {hits !== null ? <div aria-live="polite">
      <p>近似匹配 {hits.length} 页（最多 10 页） · {PDF_SEARCH_ENGINE}</p>
      {hits.length === 0 ? <p>已提取范围内未找到匹配；这不表示全书没有相关内容。</p> : <ol className="pdf-search-results">{hits.map(hit => <li key={hit.page}>
        <button type="button" className="secondary-button" onClick={() => onNavigate(hit.page)}>浏览本地 PDF 第 {hit.page} 页</button>
        <Snippet hit={hit} />
      </li>)}</ol>}
    </div> : null}
  </section>
}
