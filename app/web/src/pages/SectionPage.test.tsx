import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  MemoryRouter,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, bookApi } from '../api/client'
import type {
  LearningMode,
  LearningSlicePresentation,
  ModeItem,
  ModeResponse,
  StudyRecord,
} from '../api/types'
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

const presentationForMode = (
  mode: LearningMode,
  items: ModeItem[] = [],
): LearningSlicePresentation => {
  if (mode === 'preview') {
    return {
      schema_version: 'learning_slice_v1',
      mode: 'preview',
      overview: {
        object_count: 0,
        figure_count: 0,
        translation_available: false,
      },
      object_counts: [],
      objectives: [],
      prerequisites: { status: 'unavailable', items: [] },
      core_definitions: [],
      core_formulas: [],
      key_figures: [],
      quick_checks: [],
    }
  }
  if (mode === 'review') {
    const sourceRefs = items.map(({ kind, source_id }) => ({ kind, source_id }))
    return {
      schema_version: 'learning_slice_v1',
      mode: 'review',
      presets: [
        { id: 'one_minute', label: '1 分钟', source_refs: sourceRefs },
        { id: 'five_minute', label: '5 分钟', source_refs: sourceRefs },
        { id: 'full', label: '完整复习', source_refs: sourceRefs },
      ],
      prompts: items.map((item) => ({
        text: `先回忆「${item.title_zh || item.number || item.type_zh || '教材对象'}」的条件和结论，再显示教材内容。`,
        derivation: 'deterministic_template',
        source_ref: { kind: item.kind, source_id: item.source_id },
      })),
    }
  }
  if (mode === 'practice') {
    return {
      schema_version: 'learning_slice_v1',
      mode: 'practice',
      filters: [{ id: 'all', label: '全部', source_refs: [] }],
      items: [],
    }
  }
  return {
    schema_version: 'learning_slice_v1',
    mode: 'learn',
    groups: [],
    extensions: {
      supplementary: { status: 'unavailable' },
      lecture: { status: 'unavailable' },
    },
  }
}

const modePayload = (
  mode: LearningMode,
  items: ModeItem[] = [],
  presentation: LearningSlicePresentation = presentationForMode(mode, items),
): ModeResponse => ({
  mode,
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  chapter_id: 'chapter_01',
  section_id: 'ch01_s01',
  source_status: 'available',
  items,
  source_refs: items.map(({ kind, source_id }) => ({ kind, source_id })),
  presentation,
})

const studyRecord = (
  mode: LearningMode,
  status: 'in_progress' | 'completed' = 'in_progress',
): StudyRecord => ({
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  section_id: 'ch01_s01',
  mode,
  status,
  progress: status === 'completed' ? 100 : 0,
  started_at: '2026-08-28T01:00:00+00:00',
  last_studied_at: '2026-08-28T01:01:00+00:00',
  completed_at: status === 'completed' ? '2026-08-28T01:01:00+00:00' : null,
  updated_at: '2026-08-28T01:01:00+00:00',
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
    vi.clearAllMocks()
    vi.mocked(bookApi.getSection).mockResolvedValue(sectionResponse)
    vi.mocked(bookApi.getMode).mockImplementation(
      async (_courseId, _sectionId, mode) => modePayload(mode),
    )
    vi.mocked(bookApi.touchStudy).mockImplementation(
      async (_courseId, _sectionId, mode) => studyRecord(mode),
    )
    vi.mocked(bookApi.completeStudy).mockImplementation(
      async (_courseId, _sectionId, mode) => studyRecord(mode, 'completed'),
    )
  })

  it('exposes a scoped textbook QA entry for the current section', async () => {
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')

    expect(await screen.findByRole('heading', { name: 'L^p 空间' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '问本节内容' })).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/qa?section=ch01_s01',
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
    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '?mode=review&review_preset=full',
      )
    })
    await waitFor(() => {
      expect(bookApi.getMode).toHaveBeenLastCalledWith(
        'functional_analysis_course',
        'ch01_s01',
        'review',
      )
    })
  })

  it('renders Preview from presentation instead of locally recomputing item counts', async () => {
    const previewItem: ModeItem = {
      kind: 'object',
      source_id: 'def_preview',
      object_type: 'definition',
      type_zh: '定义',
      number: '1.1',
      title_zh: '预习定义',
      title_en: null,
      formula: null,
      printed_page: 2,
      pdf_page: 21,
      content_zh: '教材定义正文。',
      translation_available: true,
    }
    const previewPresentation: LearningSlicePresentation = {
      schema_version: 'learning_slice_v1',
      mode: 'preview',
      overview: {
        object_count: 9,
        figure_count: 4,
        translation_available: false,
      },
      object_counts: [{ object_type: 'theorem', count: 9 }],
      objectives: [
        {
          text: '理解并能复述：预习定义',
          derivation: 'deterministic_template',
          source_ref: { kind: 'object', source_id: 'def_preview' },
        },
      ],
      prerequisites: { status: 'unavailable', items: [] },
      core_definitions: [],
      core_formulas: [],
      key_figures: [],
      quick_checks: [],
    }
    vi.mocked(bookApi.getMode).mockResolvedValue(
      modePayload('preview', [previewItem], previewPresentation),
    )

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=preview')

    expect(await screen.findByRole('heading', { name: '预习概览' })).toBeInTheDocument()
    expect(screen.getByText('教材对象 9')).toBeInTheDocument()
    expect(screen.getByText('教材图示 4')).toBeInTheDocument()
    expect(screen.getByText('理解并能复述：预习定义')).toBeInTheDocument()
    expect(screen.queryByText('定义 1')).not.toBeInTheDocument()
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
    await user.click(screen.getByRole('button', { name: '显示教材内容' }))
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
    await user.click(screen.getByRole('button', { name: '显示教材内容' }))
    await user.click(screen.getByRole('link', { name: '查看教材来源' }))

    expect(
      loadSectionViewState('functional_analysis_course', 'ch01_s01', 'review'),
    ).toEqual({
      route:
        '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=full',
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
      route:
        '/courses/functional_analysis_course/sections/ch01_s01?mode=review&review_preset=full',
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

  it('touches exactly once only after the current mode payload resolves', async () => {
    let resolveMode!: (payload: ModeResponse) => void
    vi.mocked(bookApi.getMode).mockImplementation(
      () => new Promise<ModeResponse>((resolve) => { resolveMode = resolve }),
    )

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')

    await screen.findByRole('heading', { name: 'L^p 空间' })
    expect(bookApi.touchStudy).not.toHaveBeenCalled()

    resolveMode(modePayload('learn'))
    await waitFor(() => {
      expect(bookApi.touchStudy).toHaveBeenCalledTimes(1)
      expect(bookApi.touchStudy).toHaveBeenCalledWith(
        'functional_analysis_course',
        'ch01_s01',
        'learn',
      )
    })
  })

  it('does not touch progress when the mode payload fails', async () => {
    vi.mocked(bookApi.getMode).mockRejectedValue(new Error('mode unavailable'))

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')

    expect(await screen.findByText('学习内容加载失败')).toBeInTheDocument()
    expect(bookApi.touchStudy).not.toHaveBeenCalled()
  })

  it('touches preview and learn independently when the user switches modes', async () => {
    const user = userEvent.setup()
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=preview')

    await waitFor(() => {
      expect(bookApi.touchStudy).toHaveBeenCalledWith(
        'functional_analysis_course',
        'ch01_s01',
        'preview',
      )
    })

    await user.click(screen.getByRole('tab', { name: '学习' }))
    await waitFor(() => {
      expect(bookApi.touchStudy).toHaveBeenCalledWith(
        'functional_analysis_course',
        'ch01_s01',
        'learn',
      )
      expect(bookApi.touchStudy).toHaveBeenCalledTimes(2)
    })
  })

  it('shows in-progress state and completes only through the explicit action', async () => {
    const user = userEvent.setup()
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')

    expect(await screen.findByText('学习进度：进行中')).toBeInTheDocument()
    const completeButton = screen.getByRole('button', { name: '标记完成' })
    await user.click(completeButton)

    await waitFor(() => {
      expect(bookApi.completeStudy).toHaveBeenCalledTimes(1)
      expect(bookApi.completeStudy).toHaveBeenCalledWith(
        'functional_analysis_course',
        'ch01_s01',
        'learn',
      )
    })
    expect(await screen.findByText('学习进度：已完成')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '标记完成' })).not.toBeInTheDocument()
  })

  it('keeps textbook content readable when progress persistence fails and retries explicitly', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.getMode).mockResolvedValue(modePayload('learn', [reviewItem]))
    vi.mocked(bookApi.touchStudy)
      .mockRejectedValueOnce(
        new ApiError('学习进度暂无法保存', 503, 'study_store_unavailable'),
      )
      .mockResolvedValueOnce(studyRecord('learn'))

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')

    expect(await screen.findByRole('heading', { name: 'L^p 空间' })).toBeInTheDocument()
    expect(await screen.findByText('复习定理')).toBeInTheDocument()
    expect(
      await screen.findByText('学习内容仍可正常查看。学习进度暂未保存。'),
    ).toBeInTheDocument()
    expect(screen.getByText('学习进度暂无法保存')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '重试' }))

    await waitFor(() => {
      expect(bookApi.touchStudy).toHaveBeenCalledTimes(2)
      expect(
        screen.queryByText('学习内容仍可正常查看。学习进度暂未保存。'),
      ).not.toBeInTheDocument()
    })
    expect(screen.getByText('学习进度：进行中')).toBeInTheDocument()
  })
  it('renders Learn through grouped presentation without duplicating the flat object list', async () => {
    const learnItem: ModeItem = {
      kind: 'object',
      source_id: 'learn_def',
      object_type: 'definition',
      type_zh: '定义',
      number: '1.1',
      title_zh: '分组定义',
      title_en: null,
      formula: null,
      printed_page: 2,
      pdf_page: 21,
      content_zh: '分组定义正文。',
      translation_available: true,
    }
    const learnPresentation: LearningSlicePresentation = {
      schema_version: 'learning_slice_v1',
      mode: 'learn',
      groups: [
        {
          id: 'definitions',
          label: '定义 / 概念入口',
          source_refs: [{ kind: 'object', source_id: 'learn_def' }],
        },
      ],
      extensions: {
        supplementary: { status: 'unavailable' },
        lecture: { status: 'unavailable' },
      },
    }
    vi.mocked(bookApi.getMode).mockResolvedValue(
      modePayload('learn', [learnItem], learnPresentation),
    )

    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')

    expect(await screen.findByRole('heading', { name: '定义 / 概念入口' })).toBeInTheDocument()
    expect(screen.getAllByText('分组定义')).toHaveLength(1)
  })

})