import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  MemoryRouter,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { bookApi } from '../api/client'
import type { LearningMode, ModeItem, ModeResponse } from '../api/types'
import {
  loadSectionViewState,
  saveSectionViewState,
} from '../state/sectionViewState'
import { SectionPage } from './SectionPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getSection: vi.fn(),
      getMode: vi.fn(),
    },
  }
})

const sectionResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  chapter_id: 'chapter_01',
  section: {
    section_id: 'ch01_s01',
    number: '1.1',
    title_zh: 'L^p 空间',
    title_en: 'Lp spaces',
    printed_page_start: 1,
    printed_page_end: 3,
    pdf_page_start: 20,
    pdf_page_end: 22,
  },
  object_count: 2,
  figure_count: 0,
  translation_available: true,
}

const reviewItem: ModeItem = {
  kind: 'object',
  source_id: 'thm_review',
  object_type: 'theorem',
  type_zh: '定理',
  number: '1.3',
  title_zh: '复习定理',
  title_en: null,
  formula: null,
  printed_page: 3,
  pdf_page: 22,
  content_zh: '这段内容必须在用户点击后才显示。',
  translation_available: true,
}

const modePayload = (mode: LearningMode, items: ModeItem[] = []): ModeResponse => ({
  mode,
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  chapter_id: 'chapter_01',
  section_id: 'ch01_s01',
  source_status: 'available',
  items,
  source_refs: items.map(({ kind, source_id }) => ({ kind, source_id })),
})

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname}{location.search}</output>
}

function renderSection(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route
          path="/courses/:courseId/sections/:sectionId"
          element={
            <>
              <SectionPage />
              <LocationProbe />
            </>
          }
        />
        <Route
          path="/courses/:courseId/sources/:kind/:sourceId"
          element={<div>来源页</div>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SectionPage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.mocked(bookApi.getSection).mockResolvedValue(sectionResponse)
    vi.mocked(bookApi.getMode).mockImplementation(
      async (_courseId, _sectionId, mode) => modePayload(mode),
    )
  })

  it('defaults to learn with replace-style URL normalization and keeps four modes free', async () => {
    const user = userEvent.setup()
    renderSection('/courses/functional_analysis_course/sections/ch01_s01')

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '/courses/functional_analysis_course/sections/ch01_s01?mode=learn',
      )
    })

    for (const label of ['预习', '学习', '复习', '刷题']) {
      expect(screen.getByRole('tab', { name: label })).toBeEnabled()
    }

    await user.click(screen.getByRole('tab', { name: '复习' }))
    expect(screen.getByTestId('location')).toHaveTextContent('?mode=review')
    await waitFor(() => {
      expect(bookApi.getMode).toHaveBeenLastCalledWith(
        'functional_analysis_course',
        'ch01_s01',
        'review',
      )
    })
  })

  it('renders Chinese-first object content and exact missing-content fallback', async () => {
    vi.mocked(bookApi.getMode).mockResolvedValue(
      modePayload('learn', [
        {
          kind: 'object',
          source_id: 'def_lp',
          object_type: 'definition',
          type_zh: '定义',
          number: '1.1',
          title_zh: 'L^p 空间',
          title_en: 'Lp spaces',
          formula: '||f||_p < ∞',
          printed_page: 2,
          pdf_page: 21,
          content_zh: '设 f 为可测函数，并满足相应的 p 次可积条件。',
          translation_available: true,
        },
        {
          kind: 'object',
          source_id: 'thm_missing_zh',
          object_type: 'theorem',
          type_zh: '定理',
          number: '1.2',
          title_zh: '测试定理',
          title_en: 'English evidence title',
          formula: null,
          printed_page: 3,
          pdf_page: 22,
          content_zh: null,
          translation_available: true,
        },
      ]),
    )

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')

    expect(await screen.findByText('定义')).toBeInTheDocument()
    expect(screen.getAllByText('L^p 空间').length).toBeGreaterThan(0)
    expect(screen.getByText('||f||_p < ∞')).toBeInTheDocument()
    expect(
      screen.getByText('设 f 为可测函数，并满足相应的 p 次可积条件。'),
    ).toBeInTheDocument()
    expect(screen.getByText('本段中文学习内容暂未提供')).toBeInTheDocument()
  })

  it('keeps review body hidden until explicitly requested', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.getMode).mockResolvedValue(modePayload('review', [reviewItem]))

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=review')

    expect(await screen.findByText('复习定理')).toBeInTheDocument()
    expect(screen.queryByText('这段内容必须在用户点击后才显示。')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '显示内容' }))
    expect(screen.getByText('这段内容必须在用户点击后才显示。')).toBeInTheDocument()
  })

  it('renders review and practice empty payloads as normal success states', async () => {
    vi.mocked(bookApi.getMode).mockImplementation(
      async (_courseId, _sectionId, mode) => modePayload(mode),
    )

    const review = renderSection(
      '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
    )
    expect(
      await screen.findByText('本节暂无可复习的教材核心对象'),
    ).toBeInTheDocument()
    review.unmount()

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=practice')
    expect(await screen.findByText('本节暂无教材练习或习题')).toBeInTheDocument()
  })

  it('saves route, scroll, expanded items, and active source before source navigation', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.getMode).mockResolvedValue(modePayload('review', [reviewItem]))
    Object.defineProperty(window, 'scrollY', { value: 420, configurable: true })

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=review')
    await screen.findByText('复习定理')
    await user.click(screen.getByRole('button', { name: '显示内容' }))
    await user.click(screen.getByRole('link', { name: '查看教材来源' }))

    expect(
      loadSectionViewState('functional_analysis_course', 'ch01_s01', 'review'),
    ).toEqual({
      route: '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
      scrollY: 420,
      expandedSourceIds: ['thm_review'],
      activeSourceId: 'thm_review',
    })
  })

  it('restores expanded items and scroll after mode data loads', async () => {
    vi.mocked(bookApi.getMode).mockResolvedValue(modePayload('review', [reviewItem]))
    const scrollTo = vi.fn()
    Object.defineProperty(window, 'scrollTo', { value: scrollTo, configurable: true })
    saveSectionViewState('functional_analysis_course', 'ch01_s01', 'review', {
      route: '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
      scrollY: 420,
      expandedSourceIds: ['thm_review'],
      activeSourceId: 'thm_review',
    })

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=review')

    expect(
      await screen.findByText('这段内容必须在用户点击后才显示。'),
    ).toBeInTheDocument()
    await waitFor(() => {
      expect(scrollTo).toHaveBeenCalledWith({ top: 420, behavior: 'auto' })
    })
  })
})
