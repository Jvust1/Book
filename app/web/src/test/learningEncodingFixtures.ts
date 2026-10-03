import type { LearningMode, ModeResponse, SectionResponse, StudyRecord } from '../api/types'
export const learningCourse = 'original_learning_ids'
export const learningSectionId = 'original_section'
export const learningSection: SectionResponse = { course_id: learningCourse, book_id: 'original_book', chapter_id: 'original_chapter',
  section: { section_id: learningSectionId, number: '1', title_zh: 'Original learning section', title_en: null,
    printed_page_start: 'iv', printed_page_end: 'v', pdf_page_start: 2, pdf_page_end: 3 },
  object_count: 1, figure_count: 0, translation_available: true }
export const learningPayload = (mode: LearningMode, sourceId = 'original_source'): ModeResponse => ({
  course_id: learningCourse, book_id: 'original_book', chapter_id: 'original_chapter', section_id: learningSectionId,
  mode, source_status: 'available', items: [{ kind: 'object', source_id: sourceId, object_type: 'definition', type_zh: 'Original definition',
    number: '1', title_zh: 'Original learning item', title_en: null, formula: null, printed_page: 'iv', pdf_page: 2,
    content_zh: 'Original learning content.', translation_available: true }], source_refs: [{ kind: 'object', source_id: sourceId }],
})
export const learningReceipt = (mode: LearningMode): StudyRecord => ({ course_id: learningCourse, book_id: 'original_book',
  section_id: learningSectionId, mode, status: 'in_progress', progress: 0, started_at: '2026-10-01T00:00:00Z',
  last_studied_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z', completed_at: null })
