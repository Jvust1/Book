import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, bookApi } from './client'

const jsonResponse = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })

const studyRecord = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  section_id: 'ch01_s01',
  mode: 'learn',
  status: 'in_progress',
  progress: 0,
  started_at: '2026-08-28T01:00:00+00:00',
  last_studied_at: '2026-08-28T01:00:00+00:00',
  completed_at: null,
  updated_at: '2026-08-28T01:00:00+00:00',
}

describe('bookApi', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('requests a Section learning mode through the stable API path', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        mode: 'learn',
        course_id: 'functional_analysis_course',
        book_id: 'stein_shakarchi_functional_analysis_2011',
        chapter_id: 'chapter_01',
        section_id: 'ch01_s01',
        source_status: 'available',
        items: [],
        source_refs: [],
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await bookApi.getMode('functional_analysis_course', 'ch01_s01', 'learn')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/courses/functional_analysis_course/sections/ch01_s01/learn',
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })

  it('encodes course textbook search query and limit through the stable API path', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        course_id: 'functional_analysis_course',
        book_id: 'stein_shakarchi_functional_analysis_2011',
        query: 'Hölder & Banach',
        result_count: 0,
        results: [],
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await bookApi.searchCourse('functional_analysis_course', 'Hölder & Banach', 12)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/courses/functional_analysis_course/search?q=H%C3%B6lder+%26+Banach&limit=12',
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })

  it('posts a scoped conversational textbook QA request as JSON', async () => {
    const responseBody = {
      course_id: 'functional_analysis_course',
      book_id: 'stein_shakarchi_functional_analysis_2011',
      question: '那为什么必须要求完备？',
      answer: '回答',
      answer_kind: 'generated',
      answer_style: 'explain',
      scope_requested: 'section_then_book',
      scope_used: 'section',
      insufficient_evidence: false,
      message: null,
      citations: [],
    }
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(responseBody))
    vi.stubGlobal('fetch', fetchMock)

    const request = {
      question: '那为什么必须要求完备？',
      section_id: 'ch01_s01',
      history: [
        { role: 'user' as const, content: '巴拿赫空间是什么？' },
        { role: 'assistant' as const, content: '完备赋范线性空间称为巴拿赫空间。' },
      ],
    }
    const result = await bookApi.askCourse('functional_analysis_course', request)

    expect(result).toEqual(responseBody)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/courses/functional_analysis_course/qa',
      expect.objectContaining({
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'content-type': 'application/json',
        },
        body: JSON.stringify(request),
      }),
    )
  })

  it('posts StudyRecord touch without a browser identity body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(studyRecord))
    vi.stubGlobal('fetch', fetchMock)

    const result = await bookApi.touchStudy(
      'functional_analysis_course',
      'ch01_s01',
      'learn',
    )

    expect(result).toEqual(studyRecord)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/courses/functional_analysis_course/sections/ch01_s01/study/learn/touch',
      expect.objectContaining({
        method: 'POST',
        headers: { Accept: 'application/json' },
      }),
    )
    expect(fetchMock.mock.calls[0]?.[1]).not.toHaveProperty('body')
  })

  it('posts StudyRecord completion through the exact mode path', async () => {
    const completed = {
      ...studyRecord,
      mode: 'practice',
      status: 'completed',
      progress: 100,
      completed_at: '2026-08-28T01:05:00+00:00',
    }
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(completed))
    vi.stubGlobal('fetch', fetchMock)

    const result = await bookApi.completeStudy(
      'functional_analysis_course',
      'ch01_s01',
      'practice',
    )

    expect(result).toEqual(completed)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/courses/functional_analysis_course/sections/ch01_s01/study/practice/complete',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('gets all durable StudyRecords for one course', async () => {
    const responseBody = {
      course_id: 'functional_analysis_course',
      records: [studyRecord],
    }
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(responseBody))
    vi.stubGlobal('fetch', fetchMock)

    const result = await bookApi.getCourseStudyRecords('functional_analysis_course')

    expect(result).toEqual(responseBody)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/courses/functional_analysis_course/study-records',
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })

  it('gets recent StudyRecord and preserves null from a fresh store', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(null))
    vi.stubGlobal('fetch', fetchMock)

    const result = await bookApi.getRecentStudy()

    expect(result).toBeNull()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/study/recent',
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })

  it('uses the server Chinese error message for non-2xx responses', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          { error: { code: 'course_not_found', message: '课程不存在' } },
          404,
        ),
      ),
    )

    await expect(bookApi.getCourse('missing')).rejects.toMatchObject({
      name: 'ApiError',
      message: '课程不存在',
      code: 'course_not_found',
      status: 404,
    } satisfies Partial<ApiError>)
  })

  it('falls back to a Chinese generic error when the body is not usable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('broken', { status: 500 })))

    await expect(bookApi.getLibrary()).rejects.toMatchObject({
      message: '请求失败，请稍后重试',
      status: 500,
    })
  })
})
