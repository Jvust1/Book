import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { bookApi } from '../api/client'
import type { SourceResponse } from '../api/types'
import { saveSectionViewState } from '../state/sectionViewState'
import { SourcePage } from './SourcePage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getSource: vi.fn(),
    },
  }
})

const SOURCE: SourceResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  section_id: 'ch01_s01',
  kind: 'object',
  source_id: 'def_lp',
  type: 'definition',
  type_zh: '定义',
  number: '1.1',
  title_zh: 'L^p 空间',
  title_en: 'Lp spaces',
  content_zh: '这是来源中的中文教材内容。',
  formula: '||f||_p < ∞',
  printed_page: 2,
  pdf_page: 21,
  source_anchor: null,
  source_batch: 'chunk_001a',
  translation_available: true,
  context_before: [
    {
      kind: 'object',
      source_id: 'def_before',
      type: 'definition',
      number: '1.0',
      title_zh: '前一条定义',
    },
  ],
  context_after: [
    {
      kind: 'object',
      source_id: 'thm_after',
      type: 'theorem',
      number: '1.2',
      title_zh: '后一条定理',
    },
  ],
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname}{location.search}</output>
}

function renderSource() {
  return render(
    <MemoryRouter
      initialEntries={[
        '/courses/functional_analysis_course/sources/object/def_lp',
      ]}
    >
      <Routes>
        <Route
          path="/courses/:courseId/sources/:kind/:sourceId"
          element={<SourcePage />}
        />
        <Route
          path="/courses/:courseId/sections/:sectionId"
          element={<LocationProbe />}
        />
        <Route path="/courses/:courseId" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SourcePage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.mocked(bookApi.getSource).mockResolvedValue(SOURCE)
  })

  it('renders exact source pages, nullable anchor fallback, and surrounding context', async () => {
    renderSource()

    expect(await screen.findByRole('heading', { name: '教材来源' })).toBeInTheDocument()
    expect(screen.getByText('教材页：2')).toBeInTheDocument()
    expect(screen.getByText('PDF 页：21')).toBeInTheDocument()
    expect(screen.getByText('教材锚点暂未提供')).toBeInTheDocument()
    expect(screen.getByText('结构化来源：object:def_lp')).toBeInTheDocument()
    expect(screen.getByText('前一条定义')).toBeInTheDocument()
    expect(screen.getByText('后一条定理')).toBeInTheDocument()
    expect(document.querySelector('[aria-current="true"]')).not.toBeNull()
  })

  it('passes through a real source_anchor unchanged', async () => {
    vi.mocked(bookApi.getSource).mockResolvedValue({
      ...SOURCE,
      source_anchor: 'chunk_001a:p21:def_lp',
    })

    renderSource()

    expect(await screen.findByText('chunk_001a:p21:def_lp')).toBeInTheDocument()
    expect(screen.queryByText('教材锚点暂未提供')).not.toBeInTheDocument()
  })

  it('returns to the saved Section route for the active source', async () => {
    const user = userEvent.setup()
    saveSectionViewState('functional_analysis_course', 'ch01_s01', 'review', {
      route: '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
      scrollY: 420,
      expandedSourceIds: ['def_lp'],
      activeSourceId: 'def_lp',
    })

    renderSource()
    await screen.findByRole('heading', { name: '教材来源' })
    await user.click(screen.getByRole('button', { name: '返回学习' }))

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
      )
    })
  })
})
