import { Component, type ReactNode } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { ReaderTestProvider } from '../test/ReaderTestProvider'
import { encodingAnswer, encodingCourse, encodingCourseResponse, encodingQuestion, encodingSearch, encodingSource } from '../test/sourceEncodingFixtures'
import { SearchPage } from './SearchPage'
import { QAPage } from './QAPage'
import { SourcePage } from './SourcePage'
class RenderBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() { return this.state.failed ? <p>Unexpected render failure</p> : this.props.children }
}
function Destination() { const route = useLocation(); return <output data-testid="destination">{route.pathname}{route.search}</output> }
function mount(scope: 'search' | 'qa' | 'source') {
  const path = `/courses/${encodingCourse}/${scope === 'search' ? `search?q=${encodeURIComponent(encodingQuestion)}` : scope === 'qa' ? 'qa' : 'sources/object/original_source'}`
  render(<RenderBoundary><ReaderTestProvider><MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/courses/:courseId/search" element={<SearchPage />} />
    <Route path="/courses/:courseId/qa" element={<QAPage />} />
    <Route path="/courses/:courseId/sources/:kind/:sourceId" element={scope === 'source' ? <SourcePage /> : <Destination />} />
    <Route path="/courses/:courseId/sections/:sectionId" element={<Destination />} />
  </Routes></MemoryRouter></ReaderTestProvider></RenderBoundary>)
}
function responses(scope: 'search' | 'qa' | 'source', id: string) {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (input: string) => {
    const body = input.includes('/search?') ? encodingSearch(id) : input.endsWith('/qa') ? encodingAnswer(id)
      : input.includes('/sources/') ? { ...encodingSource(), section_id: id } : encodingCourseResponse
    return new Response(JSON.stringify(body), { headers: { 'content-type': 'application/json' } })
  }))
  mount(scope)
}
beforeEach(() => { sessionStorage.clear(); vi.spyOn(console, 'error').mockImplementation(() => {}) })
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })
for (const scope of ['search', 'qa', 'source'] as const) {
  it(`${scope} shows a validation failure instead of rendering or using malformed response IDs`, async () => {
    responses(scope, '\ud800')
    if (scope === 'qa') {
      fireEvent.change(screen.getByRole('textbox', { name: '教材问题' }), { target: { value: encodingQuestion } })
      fireEvent.click(screen.getByRole('button', { name: '提问' }))
    }
    expect(await screen.findByText('教材响应校验失败，请刷新后重试')).toBeInTheDocument()
    expect(screen.queryByText('Unexpected render failure')).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '查看教材来源' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '返回学习' })).not.toBeInTheDocument()
  })
  it(`${scope} preserves valid Unicode/reserved IDs in the actual navigation path`, async () => {
    const id = '原创 🧮 ?#%'
    responses(scope, id)
    if (scope === 'qa') {
      fireEvent.change(screen.getByRole('textbox', { name: '教材问题' }), { target: { value: encodingQuestion } })
      fireEvent.click(screen.getByRole('button', { name: '提问' }))
    }
    if (scope === 'source') fireEvent.click(await screen.findByRole('button', { name: '返回学习' }))
    else {
      const link = await screen.findByRole('link', { name: '查看教材来源' })
      expect(link).toHaveAttribute('href', `/courses/${encodingCourse}/sources/object/${encodeURIComponent(id)}`)
      fireEvent.click(link)
    }
    expect(await screen.findByTestId('destination')).toHaveTextContent(`/courses/${encodingCourse}/${scope === 'source' ? 'sections' : 'sources/object'}/${encodeURIComponent(id)}${scope === 'source' ? '?mode=learn' : ''}`)
    expect(screen.queryByText('Unexpected render failure')).not.toBeInTheDocument()
  })
}
