import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { encodingAnswer } from '../test/sourceEncodingFixtures'
import { buildQAEvidenceZip, QA_EXPORT_ERROR, QA_EXPORT_FILENAME } from '../export/qaEvidenceZip'
import { QAExportButton } from './QAExportButton'

vi.mock('../export/qaEvidenceZip', async () => ({
  ...await vi.importActual<typeof import('../export/qaEvidenceZip')>('../export/qaEvidenceZip'),
  buildQAEvidenceZip: vi.fn(),
}))

const response = encodingAnswer('original_source')
const props = { courseId: response.course_id, bookId: response.book_id, question: response.question,
  content: response.answer!, response, route: '/courses/original_encoding_course/qa', disabled: false }
let createUrl: ReturnType<typeof vi.fn>
let revokeUrl: ReturnType<typeof vi.fn>
let clicks: { href: string; download: string }[]

beforeEach(() => {
  clicks = []
  createUrl = vi.fn(() => 'blob:original-export')
  revokeUrl = vi.fn()
  vi.stubGlobal('URL', { createObjectURL: createUrl, revokeObjectURL: revokeUrl })
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
    clicks.push({ href: this.href, download: this.download })
  })
  vi.mocked(buildQAEvidenceZip).mockReset().mockResolvedValue(new Uint8Array([80, 75]))
})
afterEach(() => { cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('owned explicit QA download', () => {
  it('suppresses repeated clicks, downloads one local Blob and revokes it', async () => {
    vi.useFakeTimers()
    const view = render(<QAExportButton {...props} />)
    const button = screen.getByRole('button', { name: '导出本次问答 ZIP' })
    await act(async () => { fireEvent.click(button); fireEvent.click(button) })
    expect(buildQAEvidenceZip).toHaveBeenCalledTimes(1)
    expect(createUrl).toHaveBeenCalledTimes(1)
    expect(clicks).toEqual([{ href: 'blob:original-export', download: QA_EXPORT_FILENAME }])
    expect(document.querySelector('a[download]')).toBeNull()
    expect(screen.getByRole('status')).toHaveTextContent('已交给浏览器下载')
    act(() => { vi.advanceTimersByTime(1000) })
    expect(revokeUrl).toHaveBeenCalledExactlyOnceWith('blob:original-export')
    view.unmount()
    expect(revokeUrl).toHaveBeenCalledTimes(1)
  })

  it.each(['route', 'pending', 'unmount', 'replacement'] as const)('discards a completed ZIP after %s ownership changes', async change => {
    let finish!: (bytes: Uint8Array) => void
    vi.mocked(buildQAEvidenceZip).mockReturnValueOnce(new Promise(resolve => { finish = resolve }))
    const view = render(<QAExportButton {...props} />)
    fireEvent.click(screen.getByRole('button', { name: '导出本次问答 ZIP' }))
    if (change === 'unmount') view.unmount()
    else view.rerender(<QAExportButton {...props}
      route={change === 'route' ? props.route + '?section=other' : props.route}
      disabled={change === 'pending'} content={change === 'replacement' ? 'replacement' : props.content} />)
    await act(async () => finish(new Uint8Array([80, 75])))
    expect(createUrl).not.toHaveBeenCalled()
    expect(clicks).toEqual([])
    if (change === 'pending') expect(screen.getByRole('button')).toBeDisabled()
  })

  it('does not begin without current course/book context or the preceding question', () => {
    const view = render(<QAExportButton {...props} bookId={null} />)
    fireEvent.click(screen.getByRole('button'))
    view.rerender(<QAExportButton {...props} question={null} />)
    fireEvent.click(screen.getByRole('button'))
    expect(buildQAEvidenceZip).not.toHaveBeenCalled()
  })

  it('revokes immediately on unmount and reports generation failure without private detail', async () => {
    const view = render(<QAExportButton {...props} />)
    await act(async () => fireEvent.click(screen.getByRole('button')))
    view.unmount()
    expect(revokeUrl).toHaveBeenCalledExactlyOnceWith('blob:original-export')
    vi.mocked(buildQAEvidenceZip).mockRejectedValueOnce(new Error('PRIVATE_DETAIL'))
    render(<QAExportButton {...props} />)
    await act(async () => fireEvent.click(screen.getByRole('button')))
    expect(screen.getByRole('alert')).toHaveTextContent(QA_EXPORT_ERROR)
    expect(screen.queryByText('PRIVATE_DETAIL')).not.toBeInTheDocument()
    expect(createUrl).toHaveBeenCalledTimes(1)
  })
})
