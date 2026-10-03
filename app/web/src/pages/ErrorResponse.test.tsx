import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import { ReaderTestProvider } from '../test/ReaderTestProvider'
import { encodingCourse, encodingSource } from '../test/sourceEncodingFixtures'
import { SourcePage } from './SourcePage'
afterEach(() => vi.unstubAllGlobals())
function mount() {
  render(<ReaderTestProvider><MemoryRouter initialEntries={[`/courses/${encodingCourse}/sources/object/original_source`]}>
    <Routes><Route path="/courses/:courseId/sources/:kind/:sourceId" element={<SourcePage />} /></Routes>
  </MemoryRouter></ReaderTestProvider>)
}
it('displays only a bounded fallback then recovers on one explicit read, never automatic replay', async () => {
  const fetcher = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ error: {
    code: 'original_error', message: 'x'.repeat(3*1024*1024),
  } }), { status: 503, headers: { 'content-type': 'application/json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify(encodingSource()), { headers: { 'content-type': 'application/json' } }))
  vi.stubGlobal('fetch', fetcher)
  mount()
  expect(await screen.findByRole('alert')).toHaveTextContent('请求失败，请稍后重试')
  expect(document.body.textContent!.length).toBeLessThan(4096)
  expect(screen.queryByLabelText('选择本地 PDF')).not.toBeInTheDocument()
  expect(fetcher).toHaveBeenCalledOnce()
  fireEvent.click(screen.getByRole('button', { name: '重新读取' }))
  expect(await screen.findByRole('heading', { name: 'Original source' })).toBeInTheDocument()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(fetcher).toHaveBeenCalledTimes(2)
})
it('retains a valid bounded Chinese API failure instead of replacing all errors', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: {
    code: 'source_not_found', message: '教材来源不存在',
  } }), { status: 404, headers: { 'content-type': 'application/json' } })))
  mount()
  expect(await screen.findByRole('alert')).toHaveTextContent('教材来源不存在')
  expect(screen.queryByText('请求失败，请稍后重试')).not.toBeInTheDocument()
  expect(fetch).toHaveBeenCalledOnce()
})
