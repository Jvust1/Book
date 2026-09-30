import { afterEach, describe, expect, it, vi } from 'vitest'
import { bookApi } from './client'

const identity = { course_id: 'original_course', book_id: 'original_book', chapter_id: 'original_chapter' }
const section = { ...identity, section: { section_id: 'original_section', number: '1', title_zh: '原创小节', title_en: null,
  printed_page_start: 'iv', printed_page_end: 1, pdf_page_start: 2, pdf_page_end: 3 },
  object_count: 1, figure_count: 0, translation_available: true }
const item = { kind: 'object', source_id: 'original_definition', object_type: 'definition', type_zh: '定义',
  number: '1.1', title_zh: '原创定义', title_en: null, formula: 'x+x=2x', printed_page: 'iv', pdf_page: 2,
  content_zh: '原创试点内容', translation_available: true }
const mode = { ...identity, section_id: 'original_section', mode: 'learn', source_status: 'available',
  items: [item], source_refs: [{ kind: item.kind, source_id: item.source_id }] }
function respond(value: unknown) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' } })))
}
afterEach(() => vi.unstubAllGlobals())

describe('learning response route contracts', () => {
  it.each([
    { ...section, course_id: 'another_course' },
    { ...section, section: { ...section.section, section_id: 'another_section' } },
    { ...section, section: { ...section.section, pdf_page_start: -1 } },
    { ...section, section: { ...section.section, pdf_page_end: 1 } },
    { ...section, object_count: -1 },
    { ...section, unexpected: 'unvalidated metadata' },
    { ...section, section_id: 'original_section' },
  ])('rejects Section identity and shape corruption %#', async value => {
    respond(value)
    await expect(bookApi.getSection('original_course', 'original_section')).rejects.toMatchObject({ code: 'invalid_response' })
  })
  it.each([
    { ...mode, course_id: 'another_course' },
    { ...mode, section_id: 'another_section' },
    { ...mode, mode: 'practice' },
    { ...mode, items: null },
    { ...mode, items: [{ ...item, kind: 'https://untrusted.invalid' }] },
    { ...mode, source_refs: [] },
    { ...mode, source_refs: [{ kind: 'figure', source_id: item.source_id }] },
    { ...mode, items: [item, item], source_refs: [mode.source_refs[0], mode.source_refs[0]] },
    { ...mode, items: [{ ...item, pdf_page: 1.5 }] },
    { ...mode, source_status: 'broken-but-displayed' },
  ])('rejects Mode identity and source-link corruption %#', async value => {
    respond(value)
    await expect(bookApi.getMode('original_course', 'original_section', 'learn')).rejects.toMatchObject({ code: 'invalid_response' })
  })
  it('keeps Roman printed labels separate from physical page ranges', async () => {
    respond(section)
    await expect(bookApi.getSection('original_course', 'original_section')).resolves.toEqual(section)
  })
  it.each(['preview', 'learn', 'review', 'practice'] as const)('accepts exact %s content including valid empty modes', async requestedMode => {
    const value = { ...mode, mode: requestedMode }
    respond(value)
    await expect(bookApi.getMode('original_course', 'original_section', requestedMode)).resolves.toEqual(value)
    const empty = { ...value, items: [], source_refs: [] }
    respond(empty)
    await expect(bookApi.getMode('original_course', 'original_section', requestedMode)).resolves.toEqual(empty)
  })
  it('retains distinct source kinds even when IDs match', async () => {
    const value = { ...mode, items: [item, { ...item, kind: 'figure' }, { ...item, kind: 'translation' }],
      source_refs: ['object', 'figure', 'translation'].map(kind => ({ kind, source_id: item.source_id })) }
    respond(value)
    await expect(bookApi.getMode('original_course', 'original_section', 'learn')).resolves.toEqual(value)
  })
  it('bounds learning JSON before parsing or rendering source-bearing content', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', {
      headers: { 'content-type': 'application/json', 'content-length': String(2 * 1024 * 1024 + 1) } })))
    await expect(bookApi.getMode('original_course', 'original_section', 'learn')).rejects.toMatchObject({ code: 'invalid_response' })
  })

})
