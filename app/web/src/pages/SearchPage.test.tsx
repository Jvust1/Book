import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, bookApi } from '../api/client'
import type { CourseResponse, SearchResponse } from '../api/types'
import { SearchPage } from './SearchPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getCourse: vi.fn(),
      searchCourse: vi.fn(),
    },
  }
})

const COURSE: CourseResponse = {
  course: {
    course_id: 'functional_analysis_course',
    name_zh: '泛函分析：分析学进一步专题导论',
    name_en: 'Functional Analysis',
    authors: [],
    book_id: 'stein_shakarchi_functional_analysis_2011',
    chapter_count: 8,
    section_count: 132,
    runtime_status: 'READY',
  },
  chapters: [],
  section_count: 132,
}

const RESULTS: SearchResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  query: 'Hölder',
  result_count: 1,
  results: [
    {
      rank: 1,
      score: 800,
      source_kind: 'object',
      source_id: 'thm_1_1_holder',
      object_type: 'theorem',
      number: '1.1',
      title_zh: 'Hölder 不等式',
      title_en: 'Holder inequality',
      formula: null,
      pdf_page: 22,
      printed_page: 3,
      source_anchor: 'stein_shakarchi_functional_analysis_2011:pdf:22:thm_1_1_holder',
      snippet: 'Hölder 不等式',
    },
  ],
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname}{location.search}</output>
}

function renderSearch(initial = '/courses/functional_analysis_course/search') {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route path="/courses/:courseId/search" element={<SearchPage />} />
        <Route
          path="/courses/:courseId/sources/:kind/:sourceId"
          element={<LocationProbe />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(bookApi.getCourse).mockResolvedValue(COURSE)
    vi.mocked(bookApi.searchCourse).mockResolvedValue(RESULTS)
  })

  it('shows an empty-query prompt without issuing a search request', async () => {
    renderSearch()

    expect(await screen.findByRole('heading', { name: '搜索教材' })).toBeInTheDocument()
    expect(screen.getByText('泛函分析：分析学进一步专题导论')).toBeInTheDocument()
    expect(screen.getByText('输入中文、英文、定理、公式或题目关键词开始搜索')).toBeInTheDocument()
    expect(bookApi.searchCourse).not.toHaveBeenCalled()
  })

  it('uses URL q to load canonical results and source_kind for the source link', async () => {
    renderSearch('/courses/functional_analysis_course/search?q=H%C3%B6lder')

    expect(await screen.findByRole('heading', { name: 'Hölder 不等式' })).toBeInTheDocument()
    expect(bookApi.searchCourse).toHaveBeenCalledWith(
      'functional_analysis_course',
      'Hölder',
    )
    expect(screen.getByText('theorem · 1.1')).toBeInTheDocument()
    expect(screen.getByText('教材页：3')).toBeInTheDocument()
    expect(screen.getByText('PDF 页：22')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '查看教材来源' })).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/sources/object/thm_1_1_holder',
    )
  })

  it('distinguishes normal no-results from search unavailable', async () => {
    vi.mocked(bookApi.searchCourse).mockResolvedValue({
      ...RESULTS,
      query: 'nothing',
      result_count: 0,
      results: [],
    })
    renderSearch('/courses/functional_analysis_course/search?q=nothing')
    expect(await screen.findByText('未找到匹配教材内容')).toBeInTheDocument()
    expect(screen.queryByText('教材搜索暂不可用')).not.toBeInTheDocument()
  })

  it('renders a dedicated unavailable state from the stable API error code', async () => {
    vi.mocked(bookApi.searchCourse).mockRejectedValue(
      new ApiError('教材搜索暂不可用', 503, 'search_unavailable'),
    )
    renderSearch('/courses/functional_analysis_course/search?q=Banach')
    expect(await screen.findByRole('alert')).toHaveTextContent('教材搜索暂不可用')
    expect(screen.queryByText('未找到匹配教材内容')).not.toBeInTheDocument()
  })

  it('submits the input by updating canonical URL q and re-running search', async () => {
    const user = userEvent.setup()
    renderSearch()
    await screen.findByRole('heading', { name: '搜索教材' })

    await user.type(screen.getByRole('searchbox', { name: '教材搜索词' }), 'Banach space')
    await user.click(screen.getByRole('button', { name: '搜索' }))

    await waitFor(() => {
      expect(bookApi.searchCourse).toHaveBeenCalledWith(
        'functional_analysis_course',
        'Banach space',
      )
    })
  })
})
