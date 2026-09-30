import { afterEach, describe, expect, it, vi } from 'vitest'
import { bookApi } from './client'

const record = {
  course_id: 'original_course', book_id: 'original_book', section_id: 'original_section', mode: 'learn',
  status: 'in_progress', progress: 0, started_at: '2026-09-30T00:00:00+00:00',
  last_studied_at: '2026-09-30T00:00:00+00:00', completed_at: null, updated_at: '2026-09-30T00:00:00+00:00',
}
const completed = { ...record, status: 'completed', progress: 100, completed_at: '2026-09-30T00:00:00Z' }
function respond(value: unknown) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' } })))
}
afterEach(() => vi.unstubAllGlobals())

describe('StudyRecord receipt contracts', () => {
  it.each([
    { ...record, course_id: 'wrong_course' },
    { ...record, section_id: 'wrong_section' },
    { ...record, mode: 'practice' },
    { ...record, status: 'completed' },
    { ...record, progress: 100 },
    { ...record, completed_at: '2026-09-30T00:00:00Z' },
    { ...record, started_at: 'not-a-time' },
    { ...record, updated_at: '2026-09-30T00:00:00' },
    { ...record, profile_id: 'internal-identity-must-not-leak' },
    { ...record, progress: 10 },
    { ...completed, completed_at: null },
    { ...completed, progress: 0 },
  ])('rejects mismatched identity, inconsistent status or malformed receipt %#', async value => {
    respond(value)
    await expect(bookApi.touchStudy('original_course', 'original_section', 'learn')).rejects.toMatchObject({ code: 'invalid_response' })
  })
  it('does not accept an in-progress response as a confirmed completion', async () => {
    respond(record)
    await expect(bookApi.completeStudy('original_course', 'original_section', 'learn')).rejects.toMatchObject({ code: 'invalid_response' })
  })
  it.each([
    { course_id: 'wrong_course', records: [record] },
    { course_id: 'original_course', records: [{ ...record, course_id: 'wrong_course' }] },
    { course_id: 'original_course', records: [record, record] },
  ])('rejects invalid course record lists %#', async value => {
    respond(value)
    await expect(bookApi.getCourseStudyRecords('original_course')).rejects.toMatchObject({ code: 'invalid_response' })
  })
  it('rejects an invalid recent record rather than trusting a type cast', async () => {
    respond({ ...completed, mode: 'unknown' })
    await expect(bookApi.getRecentStudy()).rejects.toMatchObject({ code: 'invalid_response' })
  })
  it.each(['preview', 'learn', 'review', 'practice'] as const)('preserves valid %s progress and idempotent completed touches', async mode => {
    for (const value of [{ ...record, mode }, { ...completed, mode }]) {
      respond(value)
      await expect(bookApi.touchStudy('original_course', 'original_section', mode)).resolves.toEqual(value)
    }
    respond({ ...completed, mode })
    await expect(bookApi.completeStudy('original_course', 'original_section', mode)).resolves.toEqual({ ...completed, mode })
  })
  it('preserves aware offset timestamps without changing their meaning or normalization', async () => {
    const value = { ...record, started_at: '2026-09-30T08:00:00+08:00' }
    respond(value)
    await expect(bookApi.touchStudy('original_course', 'original_section', 'learn')).resolves.toEqual(value)
  })
  it('accepts a fresh empty recent state and distinct mode records', async () => {
    respond(null)
    await expect(bookApi.getRecentStudy()).resolves.toBeNull()
    const value = { course_id: 'original_course', records: [record, { ...record, mode: 'review' }] }
    respond(value)
    await expect(bookApi.getCourseStudyRecords('original_course')).resolves.toEqual(value)
  })
  it('never replays a mutation automatically when validation fails', async () => {
    respond({ ...completed, section_id: 'wrong_section' })
    await expect(bookApi.completeStudy('original_course', 'original_section', 'learn')).rejects.toMatchObject({ code: 'invalid_response' })
    expect(fetch).toHaveBeenCalledTimes(1)
  })
  it('uses the bounded JSON transport for mutation receipts too', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', {
      headers: { 'content-type': 'application/json', 'content-length': String(2 * 1024 * 1024 + 1) } })))
    await expect(bookApi.touchStudy('original_course', 'original_section', 'learn')).rejects.toMatchObject({ code: 'invalid_response' })
    expect(fetch).toHaveBeenCalledTimes(1)
  })

})
