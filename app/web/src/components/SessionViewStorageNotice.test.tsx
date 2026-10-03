import { act, render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { SESSION_STORAGE_NOTICE, sessionViewStorage } from '../state/sessionViewStorage'
import { SessionViewStorageNotice } from './SessionViewStorageNotice'

it('announces bounded memory-only recovery without blocking the page', async () => {
  render(<><SessionViewStorageNotice /><p>正常学习界面</p></>)
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  const get = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new DOMException('blocked', 'SecurityError') })
  try {
    await act(async () => { sessionViewStorage.read('book:qa-session:original') })
    expect(await screen.findByRole('status')).toHaveTextContent(SESSION_STORAGE_NOTICE)
    expect(screen.getByText('正常学习界面')).toBeInTheDocument()
  } finally { get.mockRestore() }
})
