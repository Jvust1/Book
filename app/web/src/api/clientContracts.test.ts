import { afterEach, describe, expect, it, vi } from 'vitest'
import { bookApi } from './client'
import { MAX_VALIDATED_RESPONSE_BYTES } from './boundedJson'

const source = {
  course_id: 'synthetic_course', book_id: 'synthetic_book', section_id: 's1', kind: 'object', source_id: 'source_1',
  type: 'definition', type_zh: '定义', number: '1', title_zh: '原创合成来源', title_en: null,
  content_zh: 'Original synthetic content.', formula: null, printed_page: 'iv', pdf_page: 3,
  source_anchor: 'synthetic:3', source_batch: 'synthetic-only', translation_available: true,
  context_before: [], context_after: [],
}
const citation = { evidence_id: 'E1', source_kind: 'object', source_id: 'source_1', chapter_id: 'ch1', section_id: 's1',
  object_type: 'definition', type_zh: '定义', number: '1', title_zh: '原创合成来源', title_en: null,
  printed_page: 'iv', pdf_page: 3, source_anchor: 'synthetic:3' }
const answer = { course_id: 'synthetic_course', book_id: 'synthetic_book', question: 'Original question?',
  answer: 'Original answer.', answer_kind: 'generated', answer_style: 'explain', scope_requested: 'section_then_book',
  scope_used: 'section', insufficient_evidence: false, message: null, citations: [citation] }
const question = { question: 'Original question?', section_id: 's1', history: [] }
const hit = { rank: 1, score: 0.5, source_kind: 'object', source_id: 'source_1', object_type: 'definition', number: '1',
  title_zh: '原创合成来源', title_en: null, formula: null, pdf_page: 3, printed_page: 'iv', source_anchor: 'synthetic:3', snippet: 'Original.' }
const search = { course_id: 'synthetic_course', book_id: 'synthetic_book', query: 'original', result_count: 1, results: [hit] }
const invalid = { name: 'ApiError', status: 200, code: 'invalid_response', message: '教材响应校验失败，请刷新后重试' }
const mock = (body: unknown) => vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply(body)))
const reply = (body: unknown) => new Response(JSON.stringify(body), { headers: { 'content-type': 'application/json' } })
afterEach(() => vi.unstubAllGlobals())

describe('source response contract boundary', () => {
  it('rejects a wrong-source 200 response before the reader receives it', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ ...source, source_id: 'different_source' })))
    await expect(bookApi.getSource('synthetic_course', 'object', 'source_1')).rejects.toMatchObject({ code: 'invalid_response' })
  })
})


describe('live Search/QA/Source JSON schema and request identity guards', () => {
  it('preserves valid source content, Roman labels and source anchors without coercion', async () => {
    mock(source)
    expect(await bookApi.getSource('synthetic_course', 'object', 'source_1')).toEqual(source)
  })
  it.each(['figure', 'translation'])('preserves supported %s source routes', async kind => {
    const data = { ...source, kind, type: kind, section_id: kind === 'translation' ? null : source.section_id }
    mock(data)
    expect(await bookApi.getSource('synthetic_course', kind, 'source_1')).toEqual(data)
  })
  it('matches the backend normalization of a requested source kind', async () => {
    mock(source)
    expect(await bookApi.getSource('synthetic_course', ' OBJECT ', 'source_1')).toEqual(source)
  })
  it.each([
    null, { ...source, course_id: 'other_course' }, { ...source, kind: 'figure' },
    { ...source, pdf_page: 0 }, { ...source, pdf_page: -1 }, { ...source, pdf_page: 1.5 },
    { ...source, pdf_page: '3' }, { ...source, raw_response: 'must not reach the reader' },
    { ...source, context_before: [{ kind: 'url', source_id: 'https://invalid.example', type: null, number: null, title_zh: null }] },
  ])('rejects invalid source identity or structure %#', async body => {
    mock(body)
    await expect(bookApi.getSource('synthetic_course', 'object', 'source_1')).rejects.toMatchObject(invalid)
  })
  it('preserves a valid generated answer with evidence and a valid system notice', async () => {
    mock(answer)
    expect(await bookApi.askCourse('synthetic_course', question)).toEqual(answer)
    const notice = { ...answer, answer: null, answer_kind: 'system_notice', answer_style: null,
      insufficient_evidence: true, message: 'No verified evidence in this synthetic fixture.', citations: [] }
    mock(notice)
    expect(await bookApi.askCourse('synthetic_course', question)).toEqual(notice)
  })
  it.each([
    { ...answer, course_id: 'other_course' }, { ...answer, question: 'Another question?' },
    { ...answer, citations: [] }, { ...answer, insufficient_evidence: true }, { ...answer, answer: '   ' },
    { ...answer, answer_kind: 'system_notice' }, { ...answer, scope_requested: 'book' },
    { ...answer, citations: [{ ...citation, section_id: 'other_section' }] },
    { ...answer, citations: [citation, citation] }, { ...answer, citations: [{ ...citation, evidence_id: '' }] },
    { ...answer, citations: [{ ...citation, source_kind: 'external_url' }] },
    { ...answer, citations: [{ ...citation, pdf_page: 0 }] }, { ...answer, prompt: 'must remain private' },
  ])('rejects malformed, unsupported or wrongly scoped QA replies %#', async body => {
    mock(body)
    await expect(bookApi.askCourse('synthetic_course', question)).rejects.toMatchObject(invalid)
  })
  it('accepts valid search data and binds the trimmed query to the request', async () => {
    mock(search)
    expect(await bookApi.searchCourse('synthetic_course', ' original ', 10)).toEqual(search)
  })
  it.each([
    { ...search, course_id: 'other_course' }, { ...search, query: 'wrong query' }, { ...search, result_count: 2 },
    { ...search, results: [{ ...hit, rank: 0 }] }, { ...search, results: [{ ...hit, rank: 2 }] },
    { ...search, result_count: 2, results: [hit, { ...hit, rank: 2 }] },
    { ...search, results: [{ ...hit, source_id: '' }] }, { ...search, results: [{ ...hit, source_kind: 'url' }] },
  ])('rejects search context, count, rank or identity corruption %#', async body => {
    mock(body)
    await expect(bookApi.searchCourse('synthetic_course', 'original', 10)).rejects.toMatchObject(invalid)
  })
  it('rejects more results than requested rather than silently truncating or re-ranking', async () => {
    mock({ ...search, result_count: 2, results: [hit, { ...hit, rank: 2, source_id: 'source_2' }] })
    await expect(bookApi.searchCourse('synthetic_course', 'original', 1)).rejects.toMatchObject(invalid)
  })
  it.each([
    new Response('{broken', { headers: { 'content-type': 'application/json' } }),
    new Response(JSON.stringify(source), { headers: { 'content-type': 'text/html' } }),
    new Response(new Uint8Array([0xff]), { headers: { 'content-type': 'application/json' } }),
    new Response('{}', { headers: { 'content-type': 'application/json', 'content-length': String(MAX_VALIDATED_RESPONSE_BYTES + 1) } }),
  ])('returns a stable error without parser or payload details %#', async response => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
    await expect(bookApi.getSource('synthetic_course', 'object', 'source_1')).rejects.toMatchObject(invalid)
  })
})
