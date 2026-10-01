import { z } from 'zod'
import type { ChapterResponse, CourseResponse, LibraryResponse } from './types'

const id = z.string().max(512).refine(value => {
  if (!value.trim()) return false
  // JSON can carry lone UTF-16 surrogates; route encoding must never throw
  // during rendering. Keep all legitimate Unicode and reserved characters.
  try { encodeURIComponent(value); return true } catch { return false }
})
const label = z.string().max(8192).nullable()
const count = z.number().int().nonnegative()
const printedPage = z.union([z.number().int(), z.string().max(256)]).nullable()
const pdfPage = z.number().int().positive().nullable()
export const sectionCardSchema = z.strictObject({
  section_id: id, number: label, title_zh: label, title_en: label,
  printed_page_start: printedPage, printed_page_end: printedPage, pdf_page_start: pdfPage, pdf_page_end: pdfPage,
}).superRefine((value, context) => {
  if (value.pdf_page_start !== null && value.pdf_page_end !== null && value.pdf_page_start > value.pdf_page_end) {
    context.addIssue({ code: 'custom', message: 'reversed physical page range' })
  }
})
const courseCard = z.strictObject({ course_id: id, book_id: id, name_zh: z.string().max(8192), name_en: label,
  authors: z.array(z.string().max(8192)).max(1024), chapter_count: count, section_count: count,
  runtime_status: z.string().max(256) })
const chapterCard = z.strictObject({ chapter_id: id, number: label, title_zh: label, title_en: label, section_count: count })
// Counts are metadata, not a promise of pagination/completeness; don't rewrite
// order or reject a valid partial catalog because a total differs from its rows.
const librarySchema = z.strictObject({ library_id: id, name: z.string().max(8192), courses: z.array(courseCard).max(10_000) })
  .refine(value => new Set(value.courses.map(row => row.course_id)).size === value.courses.length)
const courseSchema = z.strictObject({ course: courseCard, chapters: z.array(chapterCard).max(10_000), section_count: count })
  .refine(value => new Set(value.chapters.map(row => row.chapter_id)).size === value.chapters.length)
const chapterSchema = z.strictObject({ course_id: id, book_id: id, chapter: chapterCard, sections: z.array(sectionCardSchema).max(10_000) })
  .refine(value => new Set(value.sections.map(row => row.section_id)).size === value.sections.length)

export function validateLibraryResponse(value: unknown): LibraryResponse { return librarySchema.parse(value) }
export function validateCourseResponse(value: unknown, courseId: string): CourseResponse {
  const parsed = courseSchema.parse(value)
  if (parsed.course.course_id !== courseId) throw new Error('course context mismatch')
  return parsed
}
export function validateChapterResponse(value: unknown, courseId: string, chapterId: string): ChapterResponse {
  const parsed = chapterSchema.parse(value)
  if (parsed.course_id !== courseId || parsed.chapter.chapter_id !== chapterId) throw new Error('chapter context mismatch')
  return parsed
}
