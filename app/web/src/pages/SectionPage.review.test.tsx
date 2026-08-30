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
import type {
  ModeItem,
  ModeResponse,
  ReviewLearningSlicePresentation,
  StudyRecord,
} from '../api/types'
import { loadSectionViewState } from '../state/sectionViewState'
import { SectionPage } from './SectionPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getSection: vi.fn(),
      getMode: vi.fn(),
      touchStudy: vi.fn(),
      completeStudy: vi.fn(),
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
  object_count: 3,
  figure_count: 0,
  translation_available: true,
}

const items: ModeItem[] = [
  {
    kind: 'object',
    source_id: 'def_review',
    object_type: 'definition',
    type_zh: '定义',
    number: '1.1',
    title_zh: '复习定义',
    title_en: null,
    formula: null,
    printed_page: 2,
    pdf_page: 21,
    content_zh: '定义教材正文。',
    translation_available: true,
  },
  {
    kind: 'object',
    source_id: 'thm_review',
    object_type: 'theorem',
    type_zh: '定理',
    number: '1.2',
    title_zh: '复习定理',
    title_en: null,
    formula: null,
    printed_page: 3,
    pdf_page: 22,
    content_zh: '定理教材正文。',
    translation_available: true,
  },
  {
    kind: 'object',
    source_id: 'formula_review',
    object_type: 'formula',
    type_zh: '公式',
    number: '(1.3)',
    title_zh: '复习公式',
    title_en: null,
    formula: '||f||_p < ∞',
    printed_page: 3,
    pdf_page: 22,
    content_zh: '公式教材正文。',
    translation_available: true,
  },
]

const presentation: ReviewLearningSlicePresentation = {
  schema_version: 'learning_slice_v1',
  mode: 'review',
  presets: [
    {
      id: 'one_minute',
      label: '1 分钟',
      source_refs: [{ kind: 'object', source_id: 'def_review' }],
    },
    {
      id: 'five_minute',
      label: '5 分钟',
      source_refs: [
        { kind: 'object', source_id: 'def_review' },
        { kind: 'object', source_id: 'thm_review' },
      ],
    },
    {
      id: 'full',
      label: '完整复习',
      source_refs: [
        { kind: 'object', source_id: 'def_review' },
        { kind: 'object', source_id: 'thm_review' },
        { kind: 'object', source_id: 'formula_review' },
      ],
    },
  ],
  prompts: [
    {
      text: '先回忆「复习定义」的定义，再显示教材内容。',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'def_review' },
    },
    {
      text: '先回忆「复习定理」的条件和结论，再显示教材内容。',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'thm_review' },
    },
    {
      text: '先尝试写出「复习公式」，再显示教材公式。',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'formula_review' },
    },
  ],
}

const reviewPayload: ModeResponse = {
  mode: 'review',
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  chapter_id: 'chapter_01',
  section_id: 'ch01_s01',
  source_status: 'available',
  items,
  source_refs: items.map(({ kind, source_id }) => ({ kind, source_id })),
  presentation,
}

const learnPayload: ModeResponse = {
  mode: 'learn',
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  chapter_id: 'chapter_01',
  section_id: 'ch01_s01',
  source_status: 'available',
  items: [],
  source_refs: [],
  presentation: {
    schema_version: 'learning_slice_v1',
    mode: 'learn',
    groups: [],
    extensions: {
      supplementary: { status: 'unavailable' },
      lecture: { status: 'unavailable' },
    },
  },
}

const studyRecord: StudyRecord = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  section_id: 'ch01_s01',
  mode: 'review',
  status: 'in_progress',
  progress: 0,
  started_at: '2026-08-30T01:00:00+00:00',
  last_studied_at: '2026-08-30T01:00:00+00:00',
  completed_at: null,
  updated_at: '2026-08-30T01:00:00+00:00',
}

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

describe('SectionPage Review preset workflow', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.clearAllMocks()
    vi.mocked(bookApi.getSection).mockResolvedValue(sectionResponse)
    vi.mocked(bookApi.getMode).mockImplementation(async (_courseId, _sectionId, mode) =>
      mode === 'review' ? reviewPayload : learnPayload,
    )
    vi.mocked(bookApi.touchStudy).mockResolvedValue(studyRecord)
    vi.mocked(bookApi.completeStudy).mockResolvedValue({
      ...studyRecord,
      status: 'completed',
      progress: 100,
      completed_at: '2026-08-30T01:01:00+00:00',
    })
  })

  it('normalizes missing review_preset to full with replace-style URL state', async () => {
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=review')

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '?mode=review&review_preset=full',
      )
    })
    expect(await screen.findByRole('button', { name: '完整复习' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('replace-normalizes an invalid review_preset to full', async () => {
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=unknown',
    )

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '?mode=review&review_preset=full',
      )
    })
  })

  it('changes presets through URL state without touching StudyRecord again', async () => {
    const user = userEvent.setup()
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=full',
    )

    await waitFor(() => {
      expect(bookApi.touchStudy).toHaveBeenCalledTimes(1)
    })
    await user.click(screen.getByRole('button', { name: '1 分钟' }))

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '?mode=review&review_preset=one_minute',
      )
    })
    expect(bookApi.touchStudy).toHaveBeenCalledTimes(1)
    expect(bookApi.getMode).toHaveBeenCalledTimes(1)
  })

  it('renders exactly the selected five-minute Review refs', async () => {
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=five_minute',
    )

    expect(
      await screen.findByText('先回忆「复习定义」的定义，再显示教材内容。'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('先回忆「复习定理」的条件和结论，再显示教材内容。'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('先尝试写出「复习公式」，再显示教材公式。'),
    ).not.toBeInTheDocument()
  })

  it('saves selected review_preset in the source round-trip route', async () => {
    const user = userEvent.setup()
    Object.defineProperty(window, 'scrollY', { value: 321, configurable: true })
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=one_minute',
    )

    await screen.findByText('先回忆「复习定义」的定义，再显示教材内容。')
    await user.click(screen.getByRole('button', { name: '显示教材内容' }))
    await user.click(screen.getByRole('link', { name: '查看教材来源' }))

    expect(
      loadSectionViewState('functional_analysis_course', 'ch01_s01', 'review'),
    ).toEqual({
      route:
        '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=one_minute',
      scrollY: 321,
      expandedSourceIds: ['def_review'],
      activeSourceId: 'def_review',
    })
  })

  it('removes stale review_preset when switching to a non-Review mode', async () => {
    const user = userEvent.setup()
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=one_minute',
    )

    await screen.findByRole('tab', { name: '学习' })
    await user.click(screen.getByRole('tab', { name: '学习' }))

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('?mode=learn')
    })
    expect(screen.getByTestId('location')).not.toHaveTextContent('review_preset')
  })
})
