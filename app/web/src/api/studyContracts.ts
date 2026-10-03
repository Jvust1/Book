import { z } from 'zod'
import type { LearningMode, StudyRecord, StudyRecordListResponse } from './types'

export const STUDY_RECEIPT_MESSAGE = '学习进度回复无法核验，请重试或刷新核对'
const id = z.string().max(512).refine(value => !!value.trim())
const timestamp = z.iso.datetime({ offset: true }).max(64)
const base = {
  course_id: id, book_id: id, section_id: id, mode: z.enum(['preview', 'learn', 'review', 'practice']),
  started_at: timestamp, last_studied_at: timestamp, updated_at: timestamp,
}
// State consistency follows the existing 1G contract. Clock ordering is not
// inferred: a wall clock can move, and this is not a server-side migration.
export const studyRecordSchema = z.discriminatedUnion('status', [
  z.strictObject({ ...base, status: z.literal('in_progress'), progress: z.literal(0), completed_at: z.null() }),
  z.strictObject({ ...base, status: z.literal('completed'), progress: z.literal(100), completed_at: timestamp }),
])
const courseRecordsSchema = z.strictObject({ course_id: id, records: z.array(studyRecordSchema).max(10_000) })
  .superRefine((value, context) => {
    if (value.records.some(record => record.course_id !== value.course_id) ||
      new Set(value.records.map(record => JSON.stringify([record.section_id, record.mode]))).size !== value.records.length) {
      context.addIssue({ code: 'custom', message: 'record course or logical identity mismatch', path: ['records'] })
    }
  })

export function validateStudyReceipt(value: unknown, courseId: string, sectionId: string, mode: LearningMode,
  options: { bookId?: string; completed?: boolean } = {}): StudyRecord {
  const record = studyRecordSchema.parse(value)
  if (record.course_id !== courseId || record.section_id !== sectionId || record.mode !== mode ||
    (options.bookId !== undefined && record.book_id !== options.bookId) ||
    (options.completed && record.status !== 'completed')) throw new Error('study receipt context mismatch')
  return record
}
export function validateCourseStudyRecords(value: unknown, courseId: string): StudyRecordListResponse {
  const parsed = courseRecordsSchema.parse(value)
  if (parsed.course_id !== courseId) throw new Error('study course mismatch')
  return parsed
}
export function validateRecentStudy(value: unknown): StudyRecord | null {
  return value === null ? null : studyRecordSchema.parse(value)
}
