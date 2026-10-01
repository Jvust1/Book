import { afterEach, expect, it, vi } from 'vitest'
import { bookApi } from './client'

const card = { course_id: '原创 course/?#% 🧮', book_id: 'original_book', name_zh: '原创课程', name_en: null,
  authors: ['Original Author'], chapter_count: 1, section_count: 1, runtime_status: 'UNKNOWN' }
const row = { chapter_id: 'chapter /?#%', number: null, title_zh: null, title_en: null, section_count: 1 }
const section = { section_id: 'section /?#%', number: 'i', title_zh: null, title_en: null,
  printed_page_start: 'iv', printed_page_end: 1, pdf_page_start: 2, pdf_page_end: 3 }
const library = { library_id: 'original_library', name: 'Original', courses: [card] }
const course = { course: card, chapters: [row], section_count: 1 }
const chapter = { course_id: card.course_id, book_id: card.book_id, chapter: row, sections: [section] }
function respond(value: unknown) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' } })))
}
afterEach(() => vi.unstubAllGlobals())

it.each([
  { ...library, courses: null }, { ...library, courses: [card, card] },
  { ...library, courses: [{ ...card, authors: 'not an array' }] },
  { ...library, courses: [{ ...card, chapter_count: -1 }] },
  { ...library, courses: [{ ...card, course_id: '' }] }, { ...library, internal: true },
])('rejects malformed Library catalog %#', async value => {
  respond(value)
  await expect(bookApi.getLibrary()).rejects.toMatchObject({ code: 'invalid_response' })
})
it.each([
  { ...course, course: { ...card, course_id: 'wrong' } }, { ...course, chapters: [row, row] },
  { ...course, chapters: [{ ...row, section_count: 0.5 }] }, { ...course, section_count: -1 },
  { ...course, course: { ...card, book_id: '' } }, { ...course, chapters: null },
])('rejects malformed Course identity/catalog %#', async value => {
  respond(value)
  await expect(bookApi.getCourse(card.course_id)).rejects.toMatchObject({ code: 'invalid_response' })
})
it.each([
  { ...chapter, course_id: 'wrong' }, { ...chapter, chapter: { ...row, chapter_id: 'wrong' } },
  { ...chapter, sections: [section, section] }, { ...chapter, sections: [{ ...section, pdf_page_start: 0 }] },
  { ...chapter, sections: [{ ...section, pdf_page_end: 1 }] }, { ...chapter, sections: null },
])('rejects malformed Chapter identity/catalog %#', async value => {
  respond(value)
  await expect(bookApi.getChapter(card.course_id, row.chapter_id)).rejects.toMatchObject({ code: 'invalid_response' })
})
it('preserves Unicode/reserved IDs, nullable labels, Roman printed pages and original order', async () => {
  respond(library)
  await expect(bookApi.getLibrary()).resolves.toEqual(library)
  const ordered = { ...course, chapters: [row, { ...row, chapter_id: 'earlier_lexically', number: 'iv' }] }
  respond(ordered)
  await expect(bookApi.getCourse(card.course_id)).resolves.toEqual(ordered)
  expect(fetch).toHaveBeenCalledWith(`/api/courses/${encodeURIComponent(card.course_id)}`, expect.anything())
  respond(chapter)
  await expect(bookApi.getChapter(card.course_id, row.chapter_id)).resolves.toEqual(chapter)
  expect(fetch).toHaveBeenCalledWith(`/api/courses/${encodeURIComponent(card.course_id)}/chapters/${encodeURIComponent(row.chapter_id)}`, expect.anything())
})
it('accepts empty catalogs without inventing records or content', async () => {
  respond({ ...library, courses: [] }); await expect(bookApi.getLibrary()).resolves.toMatchObject({ courses: [] })
  respond({ ...course, chapters: [] }); await expect(bookApi.getCourse(card.course_id)).resolves.toMatchObject({ chapters: [] })
  respond({ ...chapter, sections: [] }); await expect(bookApi.getChapter(card.course_id, row.chapter_id)).resolves.toMatchObject({ sections: [] })
})

it('forwards caller cancellation to each read-only catalog fetch', async () => {
  const controller = new AbortController()
  for (const [value, call] of [
    [library, () => bookApi.getLibrary(controller.signal)],
    [course, () => bookApi.getCourse(card.course_id, controller.signal)],
    [chapter, () => bookApi.getChapter(card.course_id, row.chapter_id, controller.signal)],
  ] as const) {
    respond(value); await call()
    expect(fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ signal: controller.signal }))
  }
})
it('bounds catalog JSON before parsing', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', {
    headers: { 'content-type': 'application/json', 'content-length': String(2 * 1024 * 1024 + 1) } })))
  await expect(bookApi.getLibrary()).rejects.toMatchObject({ code: 'invalid_response' })
})

for (const invalidId of ['\ud800', '\udfff']) {
  it.each(['library-course', 'course-chapter', 'chapter-section'] as const)(`rejects unpaired Unicode in %s (${invalidId.charCodeAt(0).toString(16)}) before link rendering`, async location => {
    if (location === 'library-course') {
      respond({ ...library, courses: [{ ...card, course_id: invalidId }] })
      await expect(bookApi.getLibrary()).rejects.toMatchObject({ code: 'invalid_response' })
    } else if (location === 'course-chapter') {
      respond({ ...course, chapters: [{ ...row, chapter_id: invalidId }] })
      await expect(bookApi.getCourse(card.course_id)).rejects.toMatchObject({ code: 'invalid_response' })
    } else {
      respond({ ...chapter, sections: [{ ...section, section_id: invalidId }] })
      await expect(bookApi.getChapter(card.course_id, row.chapter_id)).rejects.toMatchObject({ code: 'invalid_response' })
    }
  })
}
