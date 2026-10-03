import type { CourseResponse, QAResponse, SearchResponse, SourceResponse } from '../api/types'
export const encodingCourse = 'original_encoding_course'
export const encodingQuestion = 'Original encoding question'
export const encodingCourseResponse: CourseResponse = { course: { course_id: encodingCourse, book_id: 'original_book',
  name_zh: 'Original encoding pilot', name_en: null, authors: [], chapter_count: 1, section_count: 1, runtime_status: 'READY' },
  chapters: [], section_count: 1 }
export const encodingSource = (id = 'original_source'): SourceResponse => ({
  course_id: encodingCourse, book_id: 'original_book', section_id: 'original_section', kind: 'object', source_id: id,
  type: 'definition', type_zh: 'Original definition', number: null, title_zh: 'Original source', title_en: null,
  content_zh: 'Original synthetic content.', formula: null, printed_page: 'iv', pdf_page: 2, source_anchor: null,
  source_batch: null, translation_available: true, context_before: [], context_after: [],
})
export const encodingSearch = (id: string): SearchResponse => ({ course_id: encodingCourse, book_id: 'original_book',
  query: encodingQuestion, result_count: 1, results: [{ rank: 1, score: 1, source_kind: 'object', source_id: id,
    object_type: 'definition', number: null, title_zh: 'Original search result', title_en: null, formula: null,
    pdf_page: 2, printed_page: 'iv', source_anchor: null, snippet: 'Original synthetic result.' }] })
export const encodingAnswer = (id: string): QAResponse => ({ course_id: encodingCourse, book_id: 'original_book',
  question: encodingQuestion, answer: 'Original synthetic answer.', answer_kind: 'generated', answer_style: 'brief',
  scope_requested: 'book', scope_used: 'book', insufficient_evidence: false, message: null,
  citations: [{ evidence_id: 'E1', source_kind: 'object', source_id: id, chapter_id: 'original_chapter',
    section_id: 'original_section', object_type: 'definition', type_zh: 'Original definition', number: null,
    title_zh: 'Original citation', title_en: null, printed_page: 'iv', pdf_page: 2, source_anchor: null }] })
