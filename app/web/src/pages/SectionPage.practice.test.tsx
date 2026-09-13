import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { bookApi } from '../api/client'
import type { ModeItem, ModeResponse, StudyRecord } from '../api/types'
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
    section_id: 'ch01_s08',
    number: '8',
    title_zh: '练习',
    title_en: 'Exercises',
    printed_page_start: 34,
    printed_page_end: 43,
    pdf_page_start: 53,
    pdf_page_end: 62,
  },
  object_count: 2,
  figure_count: 0,
  translation_available: true,
}

const items: ModeItem[] = [
  {
    kind: 'object',
    source_id: 'ex_practice',
    object_type: 'exercise',
    type_zh: '练习',
    number: '1',
    title_zh: '练习甲',
    title_en: null,
    formula: null,
    printed_page: 34,
    pdf_page: 53,
    content_zh: '练习甲教材正文。',
    translation_available: true,
  },
  {
    kind: 'object',
    source_id: 'prob_practice',
    object_type: 'problem',
    type_zh: '习题',
    number: '2',
    title_zh: '习题乙',
    title_en: null,
    formula: null,
    printed_page: 35,
    pdf_page: 54,
    content_zh: '习题乙教材正文。',
    translation_available: true,
  },
]

const practicePayload: ModeResponse = {
  mode: 'practice',
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  chapter_id: 'chapter_01',
  section_id: 'ch01_s08',
  source_status: 'available',
  items,
  source_refs: items.map(({ kind, source_id }) => ({ kind, source_id })),
  presentation: {
    schema_version: 'learning_slice_v1',
    mode: 'practice',
    filters: [
      {
        id: 'all',
        label: '全部',
        source_refs: [
          { kind: 'object', source_id: 'ex_practice' },
          { kind: 'object', source_id: 'prob_practice' },
        ],
      },
      {
        id: 'exercise',
        label: '练习',
        source_refs: [{ kind: 'object', source_id: 'ex_practice' }],
      },
      {
        id: 'problem',
        label: '习题',
        source_refs: [{ kind: 'object', source_id: 'prob_practice' }],
      },
    ],
    items: [
      {
        source_ref: { kind: 'object', source_id: 'ex_practice' },
        solution_status: 'unavailable',
      },
      {
        source_ref: { kind: 'object', source_id: 'prob_practice' },
        solution_status: 'unavailable',
      },
    ],
  },
}

const learnPayload: ModeResponse = {
  ...practicePayload,
  mode: 'learn',
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
  section_id: 'ch01_s08',
  mode: 'practice',
  status: 'in_progress',
  progress: 0,
  started_at: '2026-08-30T08:00:00+00:00',
  last_studied_at: '2026-08-30T08:00:00+00:00',
  completed_at: null,
  updated_at: '2026-08-30T08:00:00+00:00',
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
        <Route path="/courses/:courseId/sources/:kind/:sourceId" element={<div>来源页</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SectionPage Practice filter workflow', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    vi.clearAllMocks()
    vi.mocked(bookApi.getSection).mockResolvedValue(sectionResponse)
    vi.mocked(bookApi.getMode).mockImplementation(async (_courseId, _sectionId, mode) =>
      mode === 'practice' ? practicePayload : learnPayload,
    )
    vi.mocked(bookApi.touchStudy).mockResolvedValue(studyRecord)
    vi.mocked(bookApi.completeStudy).mockResolvedValue({
      ...studyRecord,
      status: 'completed',
      progress: 100,
      completed_at: '2026-08-30T08:01:00+00:00',
    })
  })

  it('normalizes missing practice_kind to all', async () => {
    renderSection('/courses/functional_analysis_course/sections/ch01_s08?mode=practice')

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('?mode=practice&practice_kind=all')
    })
    expect(await screen.findByRole('button', { name: '全部' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('replace-normalizes an invalid practice_kind to all', async () => {
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s08?mode=practice&practice_kind=unknown',
    )

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('?mode=practice&practice_kind=all')
    })
  })

  it('changes filters through URL state without touching StudyRecord or refetching mode', async () => {
    const user = userEvent.setup()
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s08?mode=practice&practice_kind=all',
    )

    await waitFor(() => expect(bookApi.touchStudy).toHaveBeenCalledTimes(1))
    await user.click(await screen.findByRole('button', { name: '练习' }))

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('?mode=practice&practice_kind=exercise')
    })
    expect(bookApi.touchStudy).toHaveBeenCalledTimes(1)
    expect(bookApi.getMode).toHaveBeenCalledTimes(1)
    expect(localStorage.length).toBe(0)
  })

  it('saves selected practice_kind in the source round-trip route', async () => {
    const user = userEvent.setup()
    Object.defineProperty(window, 'scrollY', { value: 456, configurable: true })
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s08?mode=practice&practice_kind=exercise',
    )

    await screen.findByText('练习甲')
    await user.click(screen.getByRole('link', { name: '查看教材来源' }))

    expect(loadSectionViewState('functional_analysis_course', 'ch01_s08', 'practice')).toEqual({
      route:
        '/courses/functional_analysis_course/sections/ch01_s08?mode=practice&practice_kind=exercise',
      scrollY: 456,
      expandedSourceIds: [],
      activeSourceId: 'ex_practice',
    })
  })

  it('removes stale practice_kind when switching away and does not carry review_preset into Practice', async () => {
    const user = userEvent.setup()
    renderSection(
      '/courses/functional_analysis_course/sections/ch01_s08?mode=practice&practice_kind=exercise&review_preset=one_minute',
    )

    await waitFor(() => {
      expect(screen.getByTestId('location')).not.toHaveTextContent('review_preset')
    })
    await user.click(await screen.findByRole('tab', { name: '学习' }))

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('?mode=learn')
    })
    expect(screen.getByTestId('location')).not.toHaveTextContent('practice_kind')
  })
})
