import { Component, type ReactNode } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import type { LearningMode } from '../api/types'
import { learningCourse, learningPayload, learningReceipt, learningSection, learningSectionId } from '../test/learningEncodingFixtures'
import { stateKey } from '../state/sectionViewState'
import { SectionPage } from './SectionPage'
class RenderBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() { return this.state.failed ? <p>Unexpected learning render failure</p> : this.props.children }
}
function Destination() { const value = useLocation(); return <output data-testid="destination">{value.pathname}{value.search}</output> }
const path = `/courses/${learningCourse}/sections/${learningSectionId}`
function mount(mode: LearningMode, sourceId = 'original_source', chapterId = 'original_chapter') {
  const fetcher = vi.fn().mockImplementation(async (input: string) => {
    const body = input.endsWith('/touch') ? learningReceipt(mode) : input.endsWith(`/sections/${learningSectionId}`)
      ? { ...learningSection, chapter_id: chapterId } : learningPayload(mode, sourceId)
    return new Response(JSON.stringify(body), { headers: { 'content-type': 'application/json' } })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RenderBoundary><MemoryRouter initialEntries={[`${path}?mode=${mode}`]}><Routes>
    <Route path="/courses/:courseId/sections/:sectionId" element={<SectionPage />} />
    <Route path="/courses/:courseId/sources/:kind/:sourceId" element={<Destination />} />
    <Route path="/courses/:courseId/chapters/:chapterId" element={<Destination />} />
  </Routes></MemoryRouter></RenderBoundary>)
  return fetcher
}
beforeEach(() => { sessionStorage.clear(); vi.spyOn(console, 'error').mockImplementation(() => {}); vi.spyOn(window, 'scrollTo').mockImplementation(() => {}) })
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })
it.each(['preview', 'learn', 'review', 'practice'] as const)('%s rejects an invalid actual Mode item before SourceLink rendering or a study touch', async mode => {
  const fetcher = mount(mode, '\ud800')
  expect(await screen.findByRole('heading', { name: '学习内容加载失败' })).toBeInTheDocument()
  expect(screen.getByText('教材响应校验失败，请刷新后重试')).toBeInTheDocument()
  expect(screen.queryByText('Unexpected learning render failure')).not.toBeInTheDocument()
  expect(screen.queryByRole('link', { name: '查看教材来源' })).not.toBeInTheDocument()
  expect(fetcher.mock.calls.filter(([url]) => url.endsWith('/touch'))).toHaveLength(0)
})
it('rejects an invalid chapter return ID before displaying Section links or touching progress', async () => {
  const fetcher = mount('learn', 'original_source', '\udfff')
  expect(await screen.findByRole('heading', { name: '小节加载失败' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: '← 返回章节' })).not.toBeInTheDocument()
  expect(fetcher.mock.calls.filter(([url]) => url.endsWith('/touch'))).toHaveLength(0)
})
it('encodes a legitimate Unicode/reserved chapter ID in the actual return link', async () => {
  const id = '原创 🧮 ?#%'
  mount('learn', 'original_source', id)
  const link = await screen.findByRole('link', { name: '← 返回章节' })
  expect(link).toHaveAttribute('href', `/courses/${learningCourse}/chapters/${encodeURIComponent(id)}`)
  fireEvent.click(link)
  expect(await screen.findByTestId('destination')).toHaveTextContent(`/courses/${learningCourse}/chapters/${encodeURIComponent(id)}`)
})
it('does not turn restored malformed/unknown view IDs into links or overwrite validated item identities', async () => {
  const id = '原创 🧮 ?#%'
  sessionStorage.setItem(stateKey(learningCourse, learningSectionId, 'review'), JSON.stringify({
    route: `${path}?mode=review`, scrollY: 0, expandedSourceIds: ['\ud800', id], activeSourceId: '\udfff',
  }))
  mount('review', id)
  expect(await screen.findByText('Original learning content.')).toBeInTheDocument()
  await waitFor(() => expect(screen.getAllByRole('link', { name: '查看教材来源' })).toHaveLength(1))
  const link = screen.getByRole('link', { name: '查看教材来源' })
  expect(link).toHaveAttribute('href', `/courses/${learningCourse}/sources/object/${encodeURIComponent(id)}`)
  fireEvent.click(link)
  expect(await screen.findByTestId('destination')).toHaveTextContent(`/courses/${learningCourse}/sources/object/${encodeURIComponent(id)}`)
})
