import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { bookApi } from '../api/client'
import { SyncPage } from './SyncPage'

vi.mock('../api/client', () => ({
  ApiError: class ApiError extends Error {},
  bookApi: { exportStudy: vi.fn(), importStudy: vi.fn() },
}))
vi.mock('../state/recorder', () => ({ isNativeRecorder: () => false, nativeCommand: vi.fn() }))

const payload = { schema_version: 'book_study_sync_v1' as const, exported_at: '2026-09-13T00:00:00+00:00', records: [] }

describe('SyncPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.mocked(bookApi.exportStudy).mockResolvedValue(payload)
    vi.mocked(bookApi.importStudy).mockResolvedValue({ imported_count: 1, skipped_count: 2, total_count: 3 })
  })

  it('exports a portable JSON progress package', async () => {
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:progress'), revokeObjectURL: vi.fn() })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    render(<SyncPage />)
    fireEvent.click(screen.getByRole('button', { name: '导出学习进度' }))
    expect(await screen.findByRole('status')).toHaveTextContent('已导出 0 条学习进度')
    expect(bookApi.exportStudy).toHaveBeenCalledOnce()
  })

  it('imports and reports merge counts', async () => {
    const { container } = render(<SyncPage />)
    const file = new File([JSON.stringify(payload)], 'progress.json', { type: 'application/json' })
    Object.defineProperty(file, 'text', { value: async () => JSON.stringify(payload) })
    fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [file] } })
    await waitFor(() => expect(bookApi.importStudy).toHaveBeenCalledWith(payload))
    expect(screen.getByRole('status')).toHaveTextContent('1 条已更新，2 条保持原值')
  })
})
