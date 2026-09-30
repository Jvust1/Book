import { ReaderTestProvider } from '../test/ReaderTestProvider'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ReaderQueryProvider } from '../state/ReaderQueryProvider'
import { createReaderQueryClient } from '../state/readerQueries'
import { ApiError, bookApi } from '../api/client'
import type { QAResponse, SourceResponse } from '../api/types'
import { saveQASessionState } from '../state/qaSessionState'
import { saveSearchViewState } from '../state/searchViewState'
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

const QA_RESPONSE: QAResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  question: '什么是 L^p 空间？',
  answer: '这是已经验证过的回答。',
  answer_kind: 'generated',
  answer_style: 'brief',
  scope_requested: 'section_then_book',
  scope_used: 'section',
  insufficient_evidence: false,
  message: null,
  citations: [
    {
      evidence_id: 'E1',
      source_kind: 'object',
      source_id: 'def_lp',
      chapter_id: 'chapter_01',
      section_id: 'ch01_s01',
      object_type: 'definition',
      type_zh: '定义',
      number: '1.1',
      title_zh: 'L^p 空间',
      title_en: 'Lp spaces',
      printed_page: 2,
      pdf_page: 21,
      source_anchor: null,
    },
  ],
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname}{location.search}</output>
}

function renderSource() {
  return render(
    <ReaderTestProvider><MemoryRouter
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
        <Route path="/courses/:courseId/search" element={<LocationProbe />} />
        <Route path="/courses/:courseId/qa" element={<LocationProbe />} />
        <Route path="/courses/:courseId" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter></ReaderTestProvider>,
  )
}

describe('SourcePage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.mocked(bookApi.getSource).mockReset().mockResolvedValue(SOURCE)
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

  it('returns to the matching QA session route including section query before stale Search and Section state', async () => {
    const user = userEvent.setup()
    saveQASessionState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/qa?section=ch01_s01',
      messages: [
        { id: 'u1', role: 'user', content: QA_RESPONSE.question },
        {
          id: 'a1',
          role: 'assistant',
          content: QA_RESPONSE.answer!,
          response: QA_RESPONSE,
        },
      ],
      scrollY: 620,
      activeCitationSourceId: 'def_lp',
    })
    saveSearchViewState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/search?q=L%5Ep',
      query: 'L^p',
      scrollY: 520,
      activeSourceKey: 'object:def_lp',
    })
    saveSectionViewState('functional_analysis_course', 'ch01_s01', 'review', {
      route: '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
      scrollY: 420,
      expandedSourceIds: ['def_lp'],
      activeSourceId: 'def_lp',
    })

    renderSource()
    await screen.findByRole('heading', { name: '教材来源' })
    await user.click(screen.getByRole('button', { name: '返回问答' }))

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '/courses/functional_analysis_course/qa?section=ch01_s01',
      )
    })
  })

  it('returns to a matching saved Search route before any Section route when QA does not match', async () => {
    const user = userEvent.setup()
    saveSearchViewState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/search?q=L%5Ep',
      query: 'L^p',
      scrollY: 520,
      activeSourceKey: 'object:def_lp',
    })
    saveSectionViewState('functional_analysis_course', 'ch01_s01', 'review', {
      route: '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
      scrollY: 420,
      expandedSourceIds: ['def_lp'],
      activeSourceId: 'def_lp',
    })

    renderSource()
    await screen.findByRole('heading', { name: '教材来源' })
    await user.click(screen.getByRole('button', { name: '返回搜索' }))

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent(
        '/courses/functional_analysis_course/search?q=L%5Ep',
      )
    })
  })

  it('returns to the saved Section route for the active source when no QA or Search state matches', async () => {
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
  it('labels cached source data during a network interruption and retries explicitly', async () => {
    const cached = { ...SOURCE, content_zh: 'LOCAL_ONLY_CACHE_VALUE' }
    vi.mocked(bookApi.getSource).mockResolvedValueOnce(cached).mockRejectedValueOnce(new TypeError('network down'))
    renderSource()
    await screen.findByText('LOCAL_ONLY_CACHE_VALUE')
    await userEvent.click(screen.getByRole('button', { name: '重新读取' }))
    expect(await screen.findByText('网络中断，当前显示本次会话缓存；内容可能已更新。')).toBeInTheDocument()
    expect(screen.getByText('LOCAL_ONLY_CACHE_VALUE')).toBeInTheDocument()
    expect(JSON.stringify(sessionStorage)).not.toContain('LOCAL_ONLY_CACHE_VALUE')
    expect(JSON.stringify(localStorage)).not.toContain('LOCAL_ONLY_CACHE_VALUE')
    await userEvent.click(screen.getByRole('button', { name: '重新读取' }))
    expect(await screen.findByText(SOURCE.content_zh!)).toBeInTheDocument()
    expect(screen.queryByText('LOCAL_ONLY_CACHE_VALUE')).not.toBeInTheDocument()
  })

  it('hides cached source content and the local PDF panel after schema or authorization rejection', async () => {
    vi.mocked(bookApi.getSource).mockResolvedValueOnce(SOURCE)
      .mockRejectedValueOnce(new ApiError('invalid source', 200, 'invalid_response'))
      .mockRejectedValueOnce(new ApiError('source forbidden', 403, 'forbidden'))
    renderSource(); await screen.findByText(SOURCE.content_zh!)
    await userEvent.click(screen.getByRole('button', { name: '重新读取' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('invalid source')
    expect(screen.queryByText(SOURCE.content_zh!)).not.toBeInTheDocument()
    expect(screen.queryByRole('region', { name: '本地 PDF 来源预览' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '重新读取' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('source forbidden')
    expect(screen.queryByText(SOURCE.content_zh!)).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '重新读取' }))
    expect(await screen.findByText(SOURCE.content_zh!)).toBeInTheDocument()
  })

  it('cancels an initial read, ignores its late response and recovers', async () => {
    let signal!: AbortSignal; let finish!: (value: SourceResponse) => void
    vi.mocked(bookApi.getSource).mockImplementationOnce((_course, _kind, _id, incoming) => {
      signal = incoming!; return new Promise(resolve => { finish = resolve })
    })
    renderSource()
    await userEvent.click(await screen.findByRole('button', { name: '取消读取' }))
    expect(signal.aborted).toBe(true)
    expect(await screen.findByText('读取已停止，请重新读取')).toBeInTheDocument()
    await act(async () => finish({ ...SOURCE, content_zh: 'ABANDONED_RESULT' }))
    expect(screen.queryByText('ABANDONED_RESULT')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '重新读取' }))
    expect(await screen.findByText(SOURCE.content_zh!)).toBeInTheDocument()
  })

  it('aborts on production-provider unmount without relying on the test wrapper cleanup', async () => {
    let signal!: AbortSignal
    vi.mocked(bookApi.getSource).mockImplementationOnce((_course, _kind, _id, incoming) => {
      signal = incoming!; return new Promise(() => {})
    })
    const client = createReaderQueryClient(Infinity)
    const view = render(<ReaderQueryProvider client={client}><MemoryRouter initialEntries={['/courses/functional_analysis_course/sources/object/def_lp']}>
      <Routes><Route path="/courses/:courseId/sources/:kind/:sourceId" element={<SourcePage />} /></Routes>
    </MemoryRouter></ReaderQueryProvider>)
    await screen.findByRole('button', { name: '取消读取' })
    view.unmount()
    expect(signal.aborted).toBe(true)
    client.clear()
  })

})
