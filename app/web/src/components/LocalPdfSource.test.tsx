import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import { loadLocalPdf, type LoadedLocalPdf } from '../pdf/localPdf'
import { LocalPdfSource } from './LocalPdfSource'

vi.mock('../pdf/localPdf', async () => ({
  ...await vi.importActual<typeof import('../pdf/localPdf')>('../pdf/localPdf'), loadLocalPdf: vi.fn(),
}))
const fakePage = () => ({
  getViewport: ({ scale }: { scale: number }) => ({ width: 600 * scale, height: 800 * scale }),
  render: vi.fn(() => ({ promise: Promise.resolve(), cancel: vi.fn() })),
  getTextContent: vi.fn(async () => ({ items: [{ str: 'SYNTHETIC PAGE TEXT' }] })),
  cleanup: vi.fn(),
})
const fakeDocument = (numPages = 3): LoadedLocalPdf => ({
  document: { numPages, getPage: vi.fn(async () => fakePage()) } as unknown as PDFDocumentProxy,
  dispose: vi.fn().mockResolvedValue(undefined),
})
const choose = (name = 'example.pdf') => fireEvent.change(screen.getByLabelText('选择本地 PDF'), {
  target: { files: [new File(['%PDF-'], name, { type: 'application/pdf' })] },
})
const props = { bookId: 'synthetic_book', sourceId: 'source_1', sourcePage: 2 }

beforeEach(() => { vi.mocked(loadLocalPdf).mockResolvedValue(fakeDocument()) })
afterEach(() => { vi.clearAllMocks() })

describe('LocalPdfSource', () => {
  it('does not load a PDF until the user selects one', () => {
    render(<LocalPdfSource {...props} />)
    expect(loadLocalPdf).not.toHaveBeenCalled()
    expect(screen.getByText(/不上传/)).toBeInTheDocument()
  })

  it('renders the source page, labels unverified identity, navigates and returns', async () => {
    const user = userEvent.setup(); const loaded = fakeDocument()
    vi.mocked(loadLocalPdf).mockResolvedValue(loaded)
    render(<LocalPdfSource {...props} />); choose()
    expect(await screen.findByText('共 3 页 · 当前浏览 第 2 页')).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText('正在显示 PDF 页…')).not.toBeInTheDocument())
    expect(screen.getByText(/尚未核验/)).toHaveTextContent('example.pdf')
    expect(loaded.document.getPage).toHaveBeenCalledWith(2)
    await user.click(screen.getByText('本页可提取文本（辅助，最多 50,000 字符）', { exact: true }))
    await user.click(screen.getByRole('button', { name: '下一页' }))
    expect(await screen.findByText('当前浏览页不是教材标注的来源页。')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('本页可提取文本（辅助，最多 50,000 字符）', { exact: true }).closest('details')).toHaveAttribute('open'))
    await user.click(screen.getByRole('button', { name: '回到来源页' }))
    expect(screen.getByText('共 3 页 · 当前浏览 第 2 页')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '关闭本地 PDF' }))
    expect(screen.queryByText(/本地文件：/)).not.toBeInTheDocument()
    expect(loaded.dispose).toHaveBeenCalledOnce()
  })

  it.each([null, 9])('requires explicit page choice for missing/out-of-range source %s', async sourcePage => {
    const loaded = fakeDocument(); vi.mocked(loadLocalPdf).mockResolvedValue(loaded)
    render(<LocalPdfSource {...props} sourcePage={sourcePage} />); choose()
    expect(await screen.findByText(/来源页号缺失或超出/)).toBeInTheDocument()
    expect(loaded.document.getPage).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: '回到来源页' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: '跳转' }))
    await waitFor(() => expect(loaded.document.getPage).toHaveBeenCalledWith(1))
  })

  it('cancels stale selection and does not replace the newer file with a delayed result', async () => {
    let resolve!: (value: LoadedLocalPdf) => void
    const old = fakeDocument(9); const current = fakeDocument(4)
    vi.mocked(loadLocalPdf).mockImplementationOnce(() => new Promise(done => { resolve = done })).mockResolvedValueOnce(current)
    render(<LocalPdfSource {...props} />); choose('old.pdf'); choose('current.pdf')
    expect(await screen.findByText('共 4 页 · 当前浏览 第 2 页')).toBeInTheDocument()
    resolve(old)
    await waitFor(() => expect(old.dispose).toHaveBeenCalledOnce())
    expect(screen.getByText(/本地文件：/)).toHaveTextContent('current.pdf')
    expect(screen.queryByText('共 9 页 · 当前浏览 第 2 页')).not.toBeInTheDocument()
  })

  it('allows retry after failure and ignores file-picker cancellation', async () => {
    vi.mocked(loadLocalPdf).mockRejectedValueOnce(new Error('PDF 无法读取')).mockResolvedValueOnce(fakeDocument())
    render(<LocalPdfSource {...props} />); choose()
    expect(await screen.findByRole('alert')).toHaveTextContent('PDF 无法读取')
    fireEvent.change(screen.getByLabelText('选择本地 PDF'), { target: { files: [] } })
    expect(loadLocalPdf).toHaveBeenCalledOnce()
    choose()
    expect(await screen.findByText('共 3 页 · 当前浏览 第 2 页')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not resurrect a file after close while loading', async () => {
    let resolve!: (value: LoadedLocalPdf) => void
    vi.mocked(loadLocalPdf).mockImplementationOnce(() => new Promise(done => { resolve = done }))
    render(<LocalPdfSource {...props} />); choose()
    await userEvent.click(screen.getByRole('button', { name: '关闭本地 PDF' }))
    const loaded = fakeDocument(); resolve(loaded)
    await waitFor(() => expect(loaded.dispose).toHaveBeenCalledOnce())
    expect(screen.queryByText(/共 \d+ 页 · 当前浏览/)).not.toBeInTheDocument()
  })
})
