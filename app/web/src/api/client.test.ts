import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, bookApi } from './client'

const jsonResponse = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })

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
