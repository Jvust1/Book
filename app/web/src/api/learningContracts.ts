import { responseIdSchema } from './responseId'
import { z } from 'zod'
import type { LearningMode, ModeResponse, SectionResponse } from './types'

// Same bounded source-bearing JSON transport and pinned Zod engine as Source/QA.
const id = responseIdSchema
const label = z.string().max(8192).nullable()
const text = z.string().max(1_000_000).nullable()
const printedPage = z.union([z.number().int(), z.string().max(256)]).nullable()
const pdfPage = z.number().int().positive().nullable()
const kind = z.enum(['object', 'figure', 'translation'])
const mode = z.enum(['preview', 'learn', 'review', 'practice'])
const identity = { course_id: id, book_id: id, chapter_id: id.nullable() }

export const sectionResponseSchema = z.strictObject({
  ...identity,
  section: z.strictObject({ section_id: id, number: label, title_zh: label, title_en: label,
    printed_page_start: printedPage, printed_page_end: printedPage, pdf_page_start: pdfPage, pdf_page_end: pdfPage }),
  object_count: z.number().int().nonnegative(), figure_count: z.number().int().nonnegative(),
  translation_available: z.boolean(),
}).superRefine((value, context) => {
  const { pdf_page_start: start, pdf_page_end: end } = value.section
  if (start !== null && end !== null && start > end) {
    context.addIssue({ code: 'custom', message: 'reversed physical page range', path: ['section'] })
  }
})
const sourceRef = z.strictObject({ kind, source_id: id })
const item = z.strictObject({ kind, source_id: id, object_type: label, type_zh: label, number: label,
  title_zh: label, title_en: label, formula: text, printed_page: printedPage, pdf_page: pdfPage,
  content_zh: text, translation_available: z.boolean() })
export const modeResponseSchema = z.strictObject({
  ...identity, section_id: id, mode, source_status: z.literal('available'),
  items: z.array(item).max(10_000), source_refs: z.array(sourceRef).max(10_000),
}).superRefine((value, context) => {
  if (value.items.length !== value.source_refs.length || value.items.some((row, index) =>
    row.kind !== value.source_refs[index]?.kind || row.source_id !== value.source_refs[index]?.source_id)) {
    context.addIssue({ code: 'custom', message: 'source references do not match displayed items', path: ['source_refs'] })
  }
  if (new Set(value.items.map(row => JSON.stringify([row.kind, row.source_id]))).size !== value.items.length) {
    context.addIssue({ code: 'custom', message: 'duplicate displayed source identity', path: ['items'] })
  }
})

export function validateSectionResponse(value: unknown, courseId: string, sectionId: string): SectionResponse {
  const parsed = sectionResponseSchema.parse(value)
  if (parsed.course_id !== courseId || parsed.section.section_id !== sectionId) throw new Error('section context mismatch')
  return parsed
}
export function validateModeResponse(value: unknown, courseId: string, sectionId: string, requestedMode: LearningMode): ModeResponse {
  const parsed = modeResponseSchema.parse(value)
  if (parsed.course_id !== courseId || parsed.section_id !== sectionId || parsed.mode !== requestedMode) {
    throw new Error('mode context mismatch')
  }
  return parsed
}
