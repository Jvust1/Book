// @vitest-environment node
import JSZip from 'jszip'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { encodingAnswer } from '../test/sourceEncodingFixtures'
import { buildQAEvidenceZip, MAX_QA_EXPORT_BYTES, QA_EXPORT_ERROR, type QAExportInput } from './qaEvidenceZip'

function input(): QAExportInput {
  const response = encodingAnswer('../原始/%?#😀')
  response.question = '为什么 e\u0301 与 😀 可以保留？\r\n第二行'
  response.answer = '原创回答：$x^2$。\n<原文> & "引号"\t\u0000'
  response.citations[0].source_anchor = 'original:页2:锚点'
  return { courseId: response.course_id, bookId: response.book_id, question: response.question,
    content: response.answer, response }
}

afterEach(() => vi.restoreAllMocks())

describe('real JSZip single-answer export', () => {
  it('round-trips exact Unicode, full response and identities using only four fixed entries', async () => {
    const value = input()
    const before = JSON.stringify(value)
    const bytes = await buildQAEvidenceZip(value)
    const zip = await JSZip.loadAsync(bytes, { checkCRC32: true })
    expect(Object.keys(zip.files).sort()).toEqual(['README.txt', 'answer.txt', 'qa-response.json', 'question.txt'])
    expect(await zip.file('question.txt')!.async('string')).toBe(value.question)
    expect(await zip.file('answer.txt')!.async('string')).toBe(value.content)
    expect(JSON.parse(await zip.file('qa-response.json')!.async('string'))).toEqual({
      schema_version: 'book.qa-evidence.v1', response: value.response,
    })
    expect(await zip.file('README.txt')!.async('string')).toContain('不证明教材版本或内容真实')
    expect(Object.values(zip.files).every(file => !file.dir && file.date.toISOString() === '1980-01-01T00:00:00.000Z')).toBe(true)
    expect(bytes[8]).toBe(0) // ZIP local-file compression method is STORE.
    expect(bytes[9]).toBe(0)
    expect(JSON.stringify(value)).toBe(before)
    expect(await buildQAEvidenceZip(value)).toEqual(bytes)
  })

  it.each(['course', 'book', 'question', 'content', 'extra', 'citation'] as const)('rejects %s mismatch before upstream generation', async field => {
    const value = input()
    if (field === 'course') value.courseId = 'other_course'
    if (field === 'book') value.bookId = 'other_book'
    if (field === 'question') value.question = 'Different question'
    if (field === 'content') value.content = 'Altered visible answer'
    if (field === 'extra') Object.assign(value.response, { private_payload: 'not an allowed field' })
    if (field === 'citation') value.response.citations = []
    const generate = vi.spyOn(JSZip.prototype, 'generateAsync')
    await expect(buildQAEvidenceZip(value)).rejects.toThrow(QA_EXPORT_ERROR)
    expect(generate).not.toHaveBeenCalled()
  })

  it('rejects a completed insufficient-evidence notice instead of calling it an answer export', async () => {
    const value = input()
    value.response = { ...value.response, answer_kind: 'system_notice', answer: null, answer_style: null,
      insufficient_evidence: true, message: 'No evidence', citations: [] }
    await expect(buildQAEvidenceZip(value)).rejects.toThrow(QA_EXPORT_ERROR)
  })

  it.each(['question', 'answer', 'source_anchor'] as const)('rejects unpaired surrogates in %s without replacement characters', async field => {
    const value = input()
    if (field === 'question') value.question = value.response.question = '\ud800'
    if (field === 'answer') value.content = value.response.answer = '\udfff'
    if (field === 'source_anchor') value.response.citations[0].source_anchor = '\ud800'
    const generate = vi.spyOn(JSZip.prototype, 'generateAsync')
    await expect(buildQAEvidenceZip(value)).rejects.toThrow(QA_EXPORT_ERROR)
    expect(generate).not.toHaveBeenCalled()
  })

  it.each(['utf8', 'json-escaping'] as const)('bounds %s bytes before ZIP generation', async kind => {
    const value = input()
    value.content = value.response.answer = kind === 'utf8' ? '界'.repeat(180_000) : '\u0000'.repeat(180_000)
    const generate = vi.spyOn(JSZip.prototype, 'generateAsync')
    await expect(buildQAEvidenceZip(value)).rejects.toThrow(QA_EXPORT_ERROR)
    expect(generate).not.toHaveBeenCalled()
  })

  it('keeps the total file payload below the declared budget', async () => {
    const value = input()
    value.content = value.response.answer = '界'.repeat(100_000)
    const zip = await JSZip.loadAsync(await buildQAEvidenceZip(value))
    const entries = await Promise.all(Object.values(zip.files).map(file => file.async('uint8array')))
    expect(entries.reduce((sum, bytes) => sum + bytes.length, 0)).toBeLessThanOrEqual(MAX_QA_EXPORT_BYTES)
  })

  it('reports a stable error without echoing upstream or answer details', async () => {
    vi.spyOn(JSZip.prototype, 'generateAsync').mockRejectedValueOnce(new Error('PRIVATE_UPSTREAM_DETAIL'))
    await expect(buildQAEvidenceZip(input())).rejects.toThrow(QA_EXPORT_ERROR)
  })
})
