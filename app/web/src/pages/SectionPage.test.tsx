import { act, render, screen, waitFor } from '@testing-library/react'
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
    expect(screen.getByText('||f||_p < ∞', { selector: 'code' })).toBeInTheDocument()
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
      await screen.findByText('学习内容仍可正常查看。学习进度保存结果尚未确认。'),
    ).toBeInTheDocument()
    expect(screen.getByText('学习进度暂无法保存')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '重试' }))

    await waitFor(() => {
      expect(bookApi.touchStudy).toHaveBeenCalledTimes(2)
      expect(
        screen.queryByText('学习内容仍可正常查看。学习进度保存结果尚未确认。'),
      ).not.toBeInTheDocument()
    })
    expect(screen.getByText('学习进度：进行中')).toBeInTheDocument()
  })
  it('does not display or record a mode for another book even with matching course and section', async () => {
    vi.mocked(bookApi.getMode).mockResolvedValue({ ...modePayload('learn', [reviewItem]), book_id: 'another_book' })
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')
    expect(await screen.findByText('学习内容与当前小节的教材身份不一致，请刷新后重试')).toBeInTheDocument()
    expect(screen.queryByText('复习定理')).not.toBeInTheDocument()
    expect(bookApi.touchStudy).not.toHaveBeenCalled()
  })

  it('waits for the section identity before displaying mode content or touching progress', async () => {
    let resolveSection!: (value: typeof sectionResponse) => void
    vi.mocked(bookApi.getSection).mockReturnValue(new Promise(resolve => { resolveSection = resolve }))
    vi.mocked(bookApi.getMode).mockResolvedValue(modePayload('learn', [reviewItem]))
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')
    await waitFor(() => expect(bookApi.getMode).toHaveBeenCalled())
    expect(screen.queryByText('复习定理')).not.toBeInTheDocument()
    expect(bookApi.touchStudy).not.toHaveBeenCalled()
    await act(async () => resolveSection(sectionResponse))
    expect(await screen.findByText('复习定理')).toBeInTheDocument()
    await waitFor(() => expect(bookApi.touchStudy).toHaveBeenCalledTimes(1))
  })

  it('ignores an old learning response arriving after a newer mode is already visible', async () => {
    let resolveLearn!: (value: ModeResponse) => void
    vi.mocked(bookApi.getMode).mockImplementation(async (_course, _section, mode) => mode === 'learn'
      ? new Promise(resolve => { resolveLearn = resolve })
      : modePayload(mode, [{ ...reviewItem, title_zh: '当前预习内容' }]))
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')
    await screen.findByRole('heading', { name: 'L^p 空间' })
    await userEvent.click(screen.getByRole('tab', { name: '预习' }))
    await screen.findByText('当前预习内容')
    await act(async () => resolveLearn(modePayload('learn', [reviewItem])))
    expect(screen.queryByText('复习定理')).not.toBeInTheDocument()
    expect(screen.getByText('当前预习内容')).toBeInTheDocument()
    expect(bookApi.touchStudy).toHaveBeenCalledTimes(1)
    expect(bookApi.touchStudy).toHaveBeenCalledWith('functional_analysis_course', 'ch01_s01', 'preview')
  })

  it.each([
    { course_id: 'wrong_course' }, { section_id: 'wrong_section' },
    { mode: 'practice' as const }, { book_id: 'wrong_book' },
  ])('does not display a progress receipt for a different context %#', async changed => {
    vi.mocked(bookApi.touchStudy).mockResolvedValue({ ...studyRecord('learn'), ...changed })
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')
    expect(await screen.findByText('学习内容仍可正常查看。学习进度保存结果尚未确认。')).toBeInTheDocument()
    expect(screen.queryByText('学习进度：进行中')).not.toBeInTheDocument()
    expect(screen.queryByText('学习进度：已完成')).not.toBeInTheDocument()
    expect(bookApi.touchStudy).toHaveBeenCalledTimes(1)
  })

  it('keeps only the last confirmed state after an invalid completion receipt and waits for explicit retry', async () => {
    vi.mocked(bookApi.completeStudy).mockResolvedValueOnce({ ...studyRecord('learn', 'completed'), book_id: 'wrong_book' })
      .mockResolvedValueOnce(studyRecord('learn', 'completed'))
    renderSection('/courses/functional_analysis_course/sections/ch01_s01?mode=learn')
    await screen.findByText('学习进度：进行中')
    await userEvent.click(screen.getByRole('button', { name: '标记完成' }))
    expect(await screen.findByText('学习内容仍可正常查看。学习进度保存结果尚未确认。')).toBeInTheDocument()
    expect(screen.getByText('上次确认进度：进行中')).toBeInTheDocument()
    expect(screen.queryByText('学习进度：已完成')).not.toBeInTheDocument()
    expect(bookApi.completeStudy).toHaveBeenCalledTimes(1)
    await userEvent.click(screen.getByRole('button', { name: '重试' }))
    expect(await screen.findByText('学习进度：已完成')).toBeInTheDocument()
    expect(screen.queryByText('学习内容仍可正常查看。学习进度保存结果尚未确认。')).not.toBeInTheDocument()
    expect(bookApi.completeStudy).toHaveBeenCalledTimes(2)
  })

})
