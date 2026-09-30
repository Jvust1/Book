import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, bookApi } from '../api/client'
import type { CourseResponse, QAResponse, SourceResponse } from '../api/types'
import {
  loadQASessionState,
  saveQASessionState,
} from '../state/qaSessionState'
import { QAPage } from './QAPage'
import { SourcePage } from './SourcePage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getCourse: vi.fn(),
      getSection: vi.fn(),
      getSource: vi.fn(),
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

const SECTION = {
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

const citation = {
  evidence_id: 'E1',
  source_kind: 'object',
  source_id: 'def_banach_space',
  chapter_id: 'chapter_01',
  section_id: 'ch01_s01',
  object_type: 'definition',
  type_zh: '定义',
  number: '1.2',
  title_zh: '巴拿赫空间',
  title_en: 'Banach space',
  printed_page: 12,
  pdf_page: 31,
  source_anchor: null,
}

const COURSE_GENERATED: QAResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  question: '什么是巴拿赫空间？',
  answer: '巴拿赫空间是完备的赋范线性空间。',
  answer_kind: 'generated',
  answer_style: 'brief',
  scope_requested: 'book',
  scope_used: 'book',
  insufficient_evidence: false,
  message: null,
  citations: [citation],
}

const SECTION_GENERATED: QAResponse = {
  ...COURSE_GENERATED,
  question: '本节里的巴拿赫空间是什么？',
  scope_requested: 'section_then_book',
  scope_used: 'section',
}

const FALLBACK_GENERATED: QAResponse = {
  ...COURSE_GENERATED,
  question: '本节之外还有什么相关定义？',
  scope_requested: 'section_then_book',
  scope_used: 'book',
}

const SECOND_GENERATED: QAResponse = {
  ...SECTION_GENERATED,
  question: '那为什么必须完备？',
  answer: '完备性保证相关极限仍留在空间中。',
  answer_style: 'explain',
}

const INSUFFICIENT: QAResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  question: '本书不存在的宇宙问题',
  answer: null,
  answer_kind: 'system_notice',
  answer_style: null,
  scope_requested: 'book',
  scope_used: 'book',
  insufficient_evidence: true,
  message: '根据当前教材中检索到的内容，暂时无法可靠回答这个问题。',
  citations: [],
}

const SOURCE: SourceResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  section_id: 'ch01_s01',
  kind: 'object',
  source_id: 'def_banach_space',
  type: 'definition',
  type_zh: '定义',
  number: '1.2',
  title_zh: '巴拿赫空间',
  title_en: 'Banach space',
  content_zh: '教材中的巴拿赫空间定义。',
  formula: null,
  printed_page: 12,
  pdf_page: 31,
  source_anchor: null,
  source_batch: 'chunk_001',
  translation_available: true,
  context_before: [],
  context_after: [],
}

function renderQA(initialEntry = '/courses/functional_analysis_course/qa') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/courses/:courseId/qa" element={<QAPage />} />
        <Route
          path="/courses/:courseId/sources/:kind/:sourceId"
          element={<SourcePage />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('QAPage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.clearAllMocks()
    vi.mocked(bookApi.getCourse).mockResolvedValue(COURSE)
    vi.mocked(bookApi.getSection).mockResolvedValue(SECTION)
    vi.mocked(bookApi.getSource).mockResolvedValue(SOURCE)
    vi.mocked(bookApi.askCourse).mockResolvedValue(COURSE_GENERATED)
    vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined)
  })

  it('shows full-book scope on the Course QA route without calling the provider on mount', async () => {
    renderQA()

    expect(await screen.findByRole('heading', { name: '教材问答' })).toBeInTheDocument()
    expect(screen.getByText('当前范围：整本教材')).toBeInTheDocument()
    expect(bookApi.getSection).not.toHaveBeenCalled()
    expect(bookApi.askCourse).not.toHaveBeenCalled()
  })

  it('loads and explains the Section-first scope from the section query', async () => {
    renderQA('/courses/functional_analysis_course/qa?section=ch01_s01')

    expect(await screen.findByText('当前范围：1.1 · L^p 空间')).toBeInTheDocument()
    expect(screen.getByText('优先本节，必要时扩展到全书')).toBeInTheDocument()
    expect(bookApi.getSection).toHaveBeenCalledWith(
      'functional_analysis_course',
      'ch01_s01',
    )
    expect(bookApi.askCourse).not.toHaveBeenCalled()
  })

  it('submits scoped QA, keeps verified citation metadata, and persists the conversation', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.askCourse).mockResolvedValue(SECTION_GENERATED)
    renderQA('/courses/functional_analysis_course/qa?section=ch01_s01')
    await screen.findByText('当前范围：1.1 · L^p 空间')

    await user.type(
      screen.getByRole('textbox', { name: '教材问题' }),
      SECTION_GENERATED.question,
    )
    await user.click(screen.getByRole('button', { name: '提问' }))

    await waitFor(() => {
      expect(bookApi.askCourse).toHaveBeenCalledWith('functional_analysis_course', {
        question: SECTION_GENERATED.question,
        section_id: 'ch01_s01',
        history: [],
      })
    })
    expect(await screen.findByText('回答依据：当前小节')).toBeInTheDocument()
    expect(screen.getByText('回答方式：简要')).toBeInTheDocument()
    expect(screen.getByText('AI 生成回答，依据下方教材来源')).toBeInTheDocument()
    expect(screen.getByText('定义 · 1.2')).toBeInTheDocument()
    expect(screen.getByText('教材页：12')).toBeInTheDocument()
    expect(screen.getByText('PDF 页：31')).toBeInTheDocument()
    expect(screen.getByText('教材锚点暂未提供')).toBeInTheDocument()

    const saved = loadQASessionState('functional_analysis_course')
    expect(saved?.route).toBe('/courses/functional_analysis_course/qa?section=ch01_s01')
    expect(saved?.messages.map(({ role }) => role)).toEqual(['user', 'assistant'])
    expect(saved?.activeCitationSourceId).toBeNull()
  })

  it('shows the whole-book fallback indicator for a Section-originated answer', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.askCourse).mockResolvedValue(FALLBACK_GENERATED)
    renderQA('/courses/functional_analysis_course/qa?section=ch01_s01')
    await screen.findByText('当前范围：1.1 · L^p 空间')

    await user.type(
      screen.getByRole('textbox', { name: '教材问题' }),
      FALLBACK_GENERATED.question,
    )
    await user.click(screen.getByRole('button', { name: '提问' }))

    expect(
      await screen.findByText('回答依据：本节 + 教材其他章节'),
    ).toBeInTheDocument()
  })

  it('sends prior user and verified assistant text as history on the second question', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.askCourse)
      .mockResolvedValueOnce(SECTION_GENERATED)
      .mockResolvedValueOnce(SECOND_GENERATED)
    renderQA('/courses/functional_analysis_course/qa?section=ch01_s01')
    await screen.findByText('当前范围：1.1 · L^p 空间')

    const input = screen.getByRole('textbox', { name: '教材问题' })
    await user.type(input, SECTION_GENERATED.question)
    await user.click(screen.getByRole('button', { name: '提问' }))
    await screen.findByText(SECTION_GENERATED.answer!, { selector: '.qa-markdown p' })

    await user.clear(input)
    await user.type(input, SECOND_GENERATED.question)
    await user.click(screen.getByRole('button', { name: '提问' }))

    await waitFor(() => {
      expect(bookApi.askCourse).toHaveBeenNthCalledWith(2, 'functional_analysis_course', {
        question: SECOND_GENERATED.question,
        section_id: 'ch01_s01',
        history: [
          { role: 'user', content: SECTION_GENERATED.question },
          { role: 'assistant', content: SECTION_GENERATED.answer },
        ],
      })
    })
    expect(await screen.findByText(SECOND_GENERATED.answer!, { selector: '.qa-markdown p' })).toBeInTheDocument()
    expect(screen.getAllByText(SECTION_GENERATED.question).length).toBeGreaterThan(0)
  })

  it('uses the server insufficient message without labeling it as a generated answer', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.askCourse).mockResolvedValue(INSUFFICIENT)
    renderQA()
    await screen.findByText('当前范围：整本教材')

    await user.type(screen.getByRole('textbox', { name: '教材问题' }), INSUFFICIENT.question)
    await user.click(screen.getByRole('button', { name: '提问' }))

    expect(await screen.findByText(INSUFFICIENT.message!)).toBeInTheDocument()
    expect(screen.queryByText('AI 生成回答，依据下方教材来源')).not.toBeInTheDocument()
  })

  it('restores QA after Source round trip with zero provider recalls', async () => {
    const user = userEvent.setup()
    saveQASessionState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/qa?section=ch01_s01',
      messages: [
        { id: 'u1', role: 'user', content: SECTION_GENERATED.question },
        {
          id: 'a1',
          role: 'assistant',
          content: SECTION_GENERATED.answer!,
          response: SECTION_GENERATED,
        },
      ],
      scrollY: 420,
      activeCitationSourceId: null,
    })

    renderQA('/courses/functional_analysis_course/qa?section=ch01_s01')

    expect(await screen.findByText(SECTION_GENERATED.answer!, { selector: '.qa-markdown p' })).toBeInTheDocument()
    expect(bookApi.askCourse).not.toHaveBeenCalled()
    await user.click(screen.getByRole('link', { name: '查看教材来源' }))

    expect(await screen.findByRole('heading', { name: '教材来源' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '返回问答' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '返回问答' }))

    expect(await screen.findByText(SECTION_GENERATED.answer!, { selector: '.qa-markdown p' })).toBeInTheDocument()
    expect(bookApi.askCourse).not.toHaveBeenCalled()
    expect(loadQASessionState('functional_analysis_course')?.activeCitationSourceId).toBe(
      'def_banach_space',
    )
  })

  it('keeps a failed user question visible and does not fabricate an assistant answer', async () => {
    const user = userEvent.setup()
    vi.mocked(bookApi.askCourse).mockRejectedValue(
      new ApiError('教材问答模型暂不可用', 503, 'qa_provider_unavailable'),
    )
    renderQA()
    await screen.findByText('当前范围：整本教材')

    const question = '失败时也要保留这个问题'
    await user.type(screen.getByRole('textbox', { name: '教材问题' }), question)
    await user.click(screen.getByRole('button', { name: '提问' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('教材问答模型暂不可用')
    expect(screen.getByText(question)).toBeInTheDocument()
    expect(screen.queryByText('AI 生成回答，依据下方教材来源')).not.toBeInTheDocument()
  })
  it('keeps a delayed old-course response out of the new course and its session', async () => {
    let resolve!: (response: QAResponse) => void
    vi.mocked(bookApi.askCourse).mockReturnValue(new Promise(done => { resolve = done }))
    function SwitchCourse() {
      const navigate = useNavigate()
      return <button onClick={() => navigate('/courses/other_synthetic_course/qa')}>切换合成课程</button>
    }
    render(<MemoryRouter initialEntries={['/courses/functional_analysis_course/qa']}>
      <SwitchCourse /><Routes><Route path="/courses/:courseId/qa" element={<QAPage />} /></Routes>
    </MemoryRouter>)
    const user = userEvent.setup()
    await user.type(screen.getByRole('textbox', { name: '教材问题' }), 'Original pending question?')
    await user.click(screen.getByRole('button', { name: '提问' }))
    await user.click(screen.getByRole('button', { name: '切换合成课程' }))
    expect(screen.queryByText('Original pending question?')).not.toBeInTheDocument()
    await act(async () => resolve({ ...COURSE_GENERATED, question: 'Original pending question?', answer: 'Original delayed answer.' }))
    expect(screen.queryByText('Original delayed answer.')).not.toBeInTheDocument()
    expect(loadQASessionState('other_synthetic_course')).toBeNull()
    expect(loadQASessionState('functional_analysis_course')?.messages).toHaveLength(1)
  })

})
