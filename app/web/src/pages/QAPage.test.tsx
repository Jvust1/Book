import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, bookApi } from '../api/client'
import type { CourseResponse, QAResponse } from '../api/types'
import { loadQAViewState, saveQAViewState } from '../state/qaViewState'
import { QAPage } from './QAPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getCourse: vi.fn(),
      askCourse: vi.fn(),
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

const GENERATED: QAResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  question: '什么是巴拿赫空间？',
  answer_kind: 'generated',
  evidence_status: 'sufficient',
  answer: '巴拿赫空间是完备的赋范线性空间。',
  citations: [
    {
      citation_id: 'C1',
      evidence_id: 'E1',
      source_kind: 'object',
      source_id: 'def_banach_space',
      object_type: 'definition',
      number: '1.2',
      title_zh: '巴拿赫空间',
      title_en: 'Banach space',
      source_anchor: 'stein_shakarchi_functional_analysis_2011:pdf:31:def_banach_space',
      pdf_page: 31,
      printed_page: 12,
    },
  ],
}

const INSUFFICIENT: QAResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  question: '本书不存在的宇宙问题',
  answer_kind: 'system_notice',
  evidence_status: 'insufficient_evidence',
  answer: '现有教材证据不足，暂不能给出可靠回答。',
  citations: [],
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname}</output>
}

function renderQA() {
  return render(
    <MemoryRouter initialEntries={['/courses/functional_analysis_course/qa']}>
      <Routes>
        <Route path="/courses/:courseId/qa" element={<QAPage />} />
        <Route path="/courses/:courseId/sources/:kind/:sourceId" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('QAPage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.clearAllMocks()
    vi.mocked(bookApi.getCourse).mockResolvedValue(COURSE)
    vi.mocked(bookApi.askCourse).mockResolvedValue(GENERATED)
  })

  it('starts empty and does not issue a QA request before submit', async () => {
    renderQA()

    expect(await screen.findByRole('heading', { name: '教材问答' })).toBeInTheDocument()
    expect(screen.getByText('泛函分析：分析学进一步专题导论')).toBeInTheDocument()
    expect(screen.getByText('输入问题后，回答只依据当前教材可验证来源。')).toBeInTheDocument()
    expect(bookApi.askCourse).not.toHaveBeenCalled()
  })

  it('submits once, exposes loading state, and renders generated answer with persistent label', async () => {
    const user = userEvent.setup()
    let resolveAnswer: ((value: QAResponse) => void) | undefined
    vi.mocked(bookApi.askCourse).mockReturnValue(
      new Promise<QAResponse>((resolve) => {
        resolveAnswer = resolve
      }),
    )
    renderQA()
    await screen.findByRole('heading', { name: '教材问答' })

    await user.type(screen.getByRole('textbox', { name: '教材问题' }), '什么是巴拿赫空间？')
    await user.click(screen.getByRole('button', { name: '提问' }))

    expect(bookApi.askCourse).toHaveBeenCalledWith('functional_analysis_course', '什么是巴拿赫空间？')
    expect(screen.getByRole('button', { name: '正在查找教材依据…' })).toBeDisabled()

    resolveAnswer?.(GENERATED)

    expect(await screen.findByText('AI 生成回答，依据下方教材来源')).toBeInTheDocument()
    expect(screen.getByText('巴拿赫空间是完备的赋范线性空间。')).toBeInTheDocument()
  })

  it('renders system notice without generated-answer label when evidence is insufficient', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.askCourse).mockResolvedValue(INSUFFICIENT)
    renderQA()
    await screen.findByRole('heading', { name: '教材问答' })

    await user.type(screen.getByRole('textbox', { name: '教材问题' }), INSUFFICIENT.question)
    await user.click(screen.getByRole('button', { name: '提问' }))

    expect(await screen.findByText('现有教材证据不足，暂不能给出可靠回答。')).toBeInTheDocument()
    expect(screen.queryByText('AI 生成回答，依据下方教材来源')).not.toBeInTheDocument()
  })

  it('shows canonical citation metadata and navigates with source_kind plus source_id', async () => {
    const user = userEvent.setup()
    renderQA()
    await screen.findByRole('heading', { name: '教材问答' })

    await user.type(screen.getByRole('textbox', { name: '教材问题' }), GENERATED.question)
    await user.click(screen.getByRole('button', { name: '提问' }))

    expect(await screen.findByRole('heading', { name: '巴拿赫空间' })).toBeInTheDocument()
    expect(screen.getByText('definition · 1.2')).toBeInTheDocument()
    expect(screen.getByText('教材页：12')).toBeInTheDocument()
    expect(screen.getByText('PDF 页：31')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '查看教材来源' })).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/sources/object/def_banach_space',
    )
  })

  it('saves only QA return context before opening a citation source', async () => {
    const user = userEvent.setup()
    Object.defineProperty(window, 'scrollY', { configurable: true, value: 735 })
    renderQA()
    await screen.findByRole('heading', { name: '教材问答' })

    await user.type(screen.getByRole('textbox', { name: '教材问题' }), GENERATED.question)
    await user.click(screen.getByRole('button', { name: '提问' }))
    await screen.findByRole('heading', { name: '巴拿赫空间' })
    await user.click(screen.getByRole('link', { name: '查看教材来源' }))

    expect(loadQAViewState('functional_analysis_course')).toEqual({
      route: '/courses/functional_analysis_course/qa',
      question: GENERATED.question,
      scrollY: 735,
      activeCitationKey: 'object:def_banach_space',
    })
  })

  it('restores saved question, re-runs QA, restores scroll, and marks the originating citation', async () => {
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined)
    saveQAViewState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/qa',
      question: GENERATED.question,
      scrollY: 420,
      activeCitationKey: 'object:def_banach_space',
    })

    renderQA()

    expect(await screen.findByDisplayValue(GENERATED.question)).toBeInTheDocument()
    await waitFor(() => {
      expect(bookApi.askCourse).toHaveBeenCalledWith(
        'functional_analysis_course',
        GENERATED.question,
      )
    })
    const citationHeading = await screen.findByRole('heading', { name: '巴拿赫空间' })
    await waitFor(() => expect(scrollTo).toHaveBeenCalledWith(0, 420))
    expect(citationHeading.closest('article')).toHaveAttribute('aria-current', 'true')
  })

  it.each([
    ['qa_unavailable', '教材问答暂不可用'],
    ['qa_provider_unavailable', '问答模型暂不可用'],
    ['qa_provider_invalid_response', '问答结果校验失败'],
  ])('renders stable error state for %s', async (code, message) => {
    const user = userEvent.setup()
    vi.mocked(bookApi.askCourse).mockRejectedValue(new ApiError(message, 503, code))
    renderQA()
    await screen.findByRole('heading', { name: '教材问答' })

    await user.type(screen.getByRole('textbox', { name: '教材问题' }), '什么是巴拿赫空间？')
    await user.click(screen.getByRole('button', { name: '提问' }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(message))
  })
})
