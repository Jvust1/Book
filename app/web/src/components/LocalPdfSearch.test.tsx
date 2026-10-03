import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { extractPdfText, type PdfTextIndex } from '../pdf/textIndex'
import { searchPdfPages, type PdfSearchHit } from '../pdf/fuzzySearch'
import { LocalPdfSearch } from './LocalPdfSearch'

vi.mock('../pdf/textIndex', async () => ({ ...await vi.importActual<typeof import('../pdf/textIndex')>('../pdf/textIndex'), extractPdfText: vi.fn() }))
vi.mock('../pdf/fuzzySearch', async () => ({ ...await vi.importActual<typeof import('../pdf/fuzzySearch')>('../pdf/fuzzySearch'), searchPdfPages: vi.fn() }))
const pdf = { numPages: 60 } as PDFDocumentProxy
const index: PdfTextIndex = { pages: [{ page: 3, text: 'original geometry', truncated: false }], start: 2, requestedEnd: 3, processedEnd: 3, limited: false }
const hit: PdfSearchHit = { page: 3, snippet: 'original geometry', before: false, after: false, marks: [[9, 17]] }
function deferred<T>() { let resolve!: (value: T) => void; return { promise: new Promise<T>(done => { resolve = done }), resolve: (value: T) => resolve(value) } }
beforeEach(() => { vi.mocked(extractPdfText).mockResolvedValue(index); vi.mocked(searchPdfPages).mockResolvedValue([hit]) })
afterEach(() => vi.clearAllMocks())

describe('LocalPdfSearch explicit actions and ephemeral state', () => {
  it('does not extract automatically, then searches and navigates only on explicit actions', async () => {
    const user = userEvent.setup(); const navigate = vi.fn()
    render(<LocalPdfSearch pdf={pdf} onNavigate={navigate} />)
    expect(extractPdfText).not.toHaveBeenCalled()
    expect(screen.getByLabelText('提取结束页')).toHaveValue(20)
    await user.clear(screen.getByLabelText('提取起始页')); await user.type(screen.getByLabelText('提取起始页'), '2')
    await user.clear(screen.getByLabelText('提取结束页')); await user.type(screen.getByLabelText('提取结束页'), '3')
    await user.click(screen.getByRole('button', { name: '提取所选页文本' }))
    expect(await screen.findByText('已提取 PDF 第 2 至 3 页 · 共 1 页有文本')).toBeInTheDocument()
    expect(extractPdfText).toHaveBeenCalledWith(pdf, 2, 3, expect.any(AbortSignal), expect.any(Function))
    await user.type(screen.getByLabelText('本地查找词'), 'geomtry')
    expect(searchPdfPages).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: '查找所选页' }))
    expect(await screen.findByText(/近似匹配 1 页/)).toBeInTheDocument()
    expect(navigate).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: '浏览本地 PDF 第 3 页' }))
    expect(navigate).toHaveBeenCalledWith(3)
  })

  it('invalidates index and results when the requested page range changes', async () => {
    render(<LocalPdfSearch pdf={pdf} onNavigate={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: '提取所选页文本' }))
    await screen.findByLabelText('本地查找词')
    fireEvent.change(screen.getByLabelText('提取结束页'), { target: { value: '5' } })
    expect(screen.queryByLabelText('本地查找词')).not.toBeInTheDocument()
    expect(screen.queryByText(/已提取 PDF/)).not.toBeInTheDocument()
  })

  it('cancels extraction, ignores late results, and allows retry', async () => {
    const pending = deferred<PdfTextIndex>(); vi.mocked(extractPdfText).mockReturnValueOnce(pending.promise)
    render(<LocalPdfSearch pdf={pdf} onNavigate={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: '提取所选页文本' })); fireEvent.click(screen.getByRole('button', { name: '提取所选页文本' }))
    expect(extractPdfText).toHaveBeenCalledOnce()
    const signal = vi.mocked(extractPdfText).mock.calls[0][3]
    await userEvent.click(screen.getByRole('button', { name: '取消本地查找' }))
    expect(signal.aborted).toBe(true)
    pending.resolve(index); await Promise.resolve()
    expect(screen.queryByLabelText('本地查找词')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '提取所选页文本' }))
    expect(await screen.findByLabelText('本地查找词')).toBeInTheDocument()
  })

  it('clear cancels a pending search and stale hits cannot become navigable', async () => {
    const pending = deferred<PdfSearchHit[]>(); vi.mocked(searchPdfPages).mockReturnValue(pending.promise)
    render(<LocalPdfSearch pdf={pdf} onNavigate={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: '提取所选页文本' }))
    await userEvent.type(await screen.findByLabelText('本地查找词'), 'geomtry')
    await userEvent.click(screen.getByRole('button', { name: '查找所选页' }))
    const signal = vi.mocked(searchPdfPages).mock.calls[0][2]
    await userEvent.click(screen.getByRole('button', { name: '清空本地索引' }))
    expect(signal.aborted).toBe(true)
    pending.resolve([hit]); await Promise.resolve()
    expect(screen.queryByRole('button', { name: /浏览本地 PDF 第/ })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('本地查找词')).not.toBeInTheDocument()
  })

  it('unmount aborts pending extraction', async () => {
    vi.mocked(extractPdfText).mockReturnValue(new Promise(() => {}))
    const view = render(<LocalPdfSearch pdf={pdf} onNavigate={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: '提取所选页文本' }))
    const signal = vi.mocked(extractPdfText).mock.calls[0][3]
    view.unmount(); expect(signal.aborted).toBe(true)
  })

  it('keeps empty and truncated scopes explicit', async () => {
    vi.mocked(extractPdfText).mockResolvedValue({ ...index, pages: [{ page: 2, text: '', truncated: true }], processedEnd: 2, limited: true })
    render(<LocalPdfSearch pdf={pdf} onNavigate={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: '提取所选页文本' }))
    expect(await screen.findByText(/所选页没有可提取文本/)).toBeInTheDocument()
    expect(screen.getByText(/提取达到字符上限/)).toBeInTheDocument()
    expect(screen.queryByLabelText('本地查找词')).not.toBeInTheDocument()
  })

  it('renders malicious-looking source snippets as inert text', async () => {
    vi.mocked(searchPdfPages).mockResolvedValue([{ ...hit, snippet: '<img src=x onerror=alert(1)>', marks: [] }])
    const view = render(<LocalPdfSearch pdf={pdf} onNavigate={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: '提取所选页文本' }))
    await userEvent.type(await screen.findByLabelText('本地查找词'), 'geomtry')
    await userEvent.click(screen.getByRole('button', { name: '查找所选页' }))
    await waitFor(() => expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeInTheDocument())
    expect(view.container.querySelector('img')).toBeNull()
  })
})
