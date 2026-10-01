import { z } from 'zod'
import type { QARequest, QAResponse, SearchResponse, SourceResponse } from './types'

export const RESPONSE_CONTRACT_ENGINE = 'zod@4.6.5'
const id = z.string().max(512).refine(value => {
  if (!value.trim()) return false
  // JSON may contain lone UTF-16 surrogates. Reject them before any source,
  // citation or return-route ID reaches encodeURIComponent; never remap IDs.
  try { encodeURIComponent(value); return true } catch { return false }
})
const label = z.string().max(8192)
const nullableLabel = label.nullable()
const nullableText = z.string().max(1_000_000).nullable()
const kind = z.enum(['object', 'figure', 'translation'])
const printedPage = z.union([z.number().int(), z.string().max(256)]).nullable()
const pdfPage = z.number().int().positive().nullable()

export const citationSchema = z.strictObject({
  evidence_id: id, source_kind: kind, source_id: id, chapter_id: id.nullable(), section_id: id.nullable(),
  object_type: nullableLabel, type_zh: nullableLabel, number: nullableLabel, title_zh: nullableLabel,
  title_en: nullableLabel, printed_page: printedPage, pdf_page: pdfPage, source_anchor: nullableLabel,
})
const qaBase = {
  course_id: id, book_id: id, question: z.string().max(100_000).refine(value => !!value.trim()),
  scope_requested: z.enum(['book', 'section_then_book']), scope_used: z.enum(['section', 'book']),
}
export const qaResponseSchema = z.discriminatedUnion('answer_kind', [
  z.strictObject({ ...qaBase, answer_kind: z.literal('generated'),
    answer: z.string().max(1_000_000).refine(value => !!value.trim()),
    answer_style: z.enum(['brief', 'explain', 'compare', 'proof']), insufficient_evidence: z.literal(false),
    message: z.null(), citations: z.array(citationSchema).min(1).max(1000) }),
  z.strictObject({ ...qaBase, answer_kind: z.literal('system_notice'), answer: z.null(), answer_style: z.null(),
    insufficient_evidence: z.literal(true), message: z.string().max(100_000).refine(value => !!value.trim()),
    citations: z.array(citationSchema).length(0) }),
]).superRefine((value, context) => {
  if (value.scope_requested === 'book' && value.scope_used !== 'book') {
    context.addIssue({ code: 'custom', message: 'inconsistent scope', path: ['scope_used'] })
  }
  if (new Set(value.citations.map(citation => citation.evidence_id)).size !== value.citations.length) {
    context.addIssue({ code: 'custom', message: 'duplicate evidence identity', path: ['citations'] })
  }
})

const contextSchema = z.strictObject({ kind, source_id: id, type: nullableLabel, number: nullableLabel, title_zh: nullableLabel })
export const sourceResponseSchema = z.strictObject({
  course_id: id, book_id: id, section_id: id.nullable(), kind, source_id: id, type: nullableLabel,
  type_zh: label, number: nullableLabel, title_zh: nullableLabel, title_en: nullableLabel,
  content_zh: nullableText, formula: nullableText, printed_page: printedPage, pdf_page: pdfPage,
  source_anchor: nullableLabel, source_batch: nullableLabel, translation_available: z.boolean(),
  context_before: z.array(contextSchema).max(1000), context_after: z.array(contextSchema).max(1000),
})
const searchItemSchema = z.strictObject({
  rank: z.number().int().positive(), score: z.number(), source_kind: kind, source_id: id,
  object_type: nullableLabel, number: nullableLabel, title_zh: nullableLabel, title_en: nullableLabel,
  formula: nullableText, pdf_page: pdfPage, printed_page: printedPage, source_anchor: nullableLabel, snippet: nullableText,
})
export const searchResponseSchema = z.strictObject({
  course_id: id, book_id: id, query: z.string().max(100_000), result_count: z.number().int().nonnegative(),
  results: z.array(searchItemSchema).max(1000),
}).superRefine((value, context) => {
  if (value.result_count !== value.results.length || value.results.some((item, index) => item.rank !== index + 1)) {
    context.addIssue({ code: 'custom', message: 'inconsistent result count or rank', path: ['results'] })
  }
  const identities = value.results.map(item => JSON.stringify([item.source_kind, item.source_id]))
  if (new Set(identities).size !== identities.length) {
    context.addIssue({ code: 'custom', message: 'duplicate source identity', path: ['results'] })
  }
})

function requireMatch(condition: boolean): void { if (!condition) throw new Error('response context mismatch') }
export function validateSourceResponse(value: unknown, courseId: string, sourceKind: string, sourceId: string): SourceResponse {
  const parsed = sourceResponseSchema.parse(value)
  requireMatch(parsed.course_id === courseId && parsed.kind === sourceKind.trim().toLowerCase() && parsed.source_id === sourceId)
  return parsed
}
export function validateSearchResponse(value: unknown, courseId: string, query: string, limit: number): SearchResponse {
  const parsed = searchResponseSchema.parse(value)
  requireMatch(parsed.course_id === courseId && parsed.query === query.trim() && parsed.results.length <= limit)
  return parsed
}
export function validateQAResponse(value: unknown, courseId: string, request: QARequest): QAResponse {
  const parsed = qaResponseSchema.parse(value)
  const section = request.section_id?.trim() || null
  requireMatch(parsed.course_id === courseId && parsed.question === request.question.trim() &&
    parsed.scope_requested === (section ? 'section_then_book' : 'book'))
  if (parsed.scope_used === 'section') requireMatch(parsed.citations.every(citation => citation.section_id === section))
  return parsed
}
