export type LearningMode = 'preview' | 'learn' | 'review' | 'practice'

export interface CourseCard {
  course_id: string
  name_zh: string
  name_en: string | null
  authors: string[]
  book_id: string
  chapter_count: number
  section_count: number
  runtime_status: string
}

export interface LibraryResponse {
  library_id: string
  name: string
  courses: CourseCard[]
}

export interface SectionCard {
  section_id: string
  number: string | null
  title_zh: string | null
  title_en: string | null
  printed_page_start: number | string | null
  printed_page_end: number | string | null
  pdf_page_start: number | null
  pdf_page_end: number | null
}

export interface ChapterCard {
  chapter_id: string
  number: string | null
  title_zh: string | null
  title_en: string | null
  section_count: number
}

export interface CourseResponse {
  course: CourseCard
  chapters: ChapterCard[]
  section_count: number
}

export interface ChapterResponse {
  course_id: string
  book_id: string
  chapter: ChapterCard
  sections: SectionCard[]
}

export interface SectionResponse {
  course_id: string
  book_id: string
  chapter_id: string | null
  section: SectionCard
  object_count: number
  figure_count: number
  translation_available: boolean
}

export interface ModeItem {
  kind: string
  source_id: string
  object_type: string | null
  type_zh: string | null
  number: string | null
  title_zh: string | null
  title_en: string | null
  formula: string | null
  printed_page: number | string | null
  pdf_page: number | null
  content_zh: string | null
  translation_available: boolean
}

export interface SourceRef {
  kind: string
  source_id: string
}

export interface ModeResponse {
  mode: LearningMode
  course_id: string
  book_id: string
  chapter_id: string | null
  section_id: string
  source_status: string
  items: ModeItem[]
  source_refs: SourceRef[]
}

export interface SourceContextItem {
  kind: string
  source_id: string
  type: string | null
  number: string | null
  title_zh: string | null
}

export interface SourceResponse {
  course_id: string
  book_id: string
  section_id: string | null
  kind: string
  source_id: string
  type: string | null
  type_zh: string
  number: string | null
  title_zh: string | null
  title_en: string | null
  content_zh: string | null
  formula: string | null
  printed_page: number | string | null
  pdf_page: number | null
  source_anchor: string | null
  source_batch: string | null
  translation_available: boolean
  context_before: SourceContextItem[]
  context_after: SourceContextItem[]
}

export interface SearchResultItem {
  rank: number
  score: number
  source_kind: string
  source_id: string
  object_type: string | null
  number: string | null
  title_zh: string | null
  title_en: string | null
  formula: string | null
  pdf_page: number | null
  printed_page: number | string | null
  source_anchor: string | null
  snippet: string | null
}

export interface SearchResponse {
  course_id: string
  book_id: string
  query: string
  result_count: number
  results: SearchResultItem[]
}

export type QAAnswerStyle = 'brief' | 'explain' | 'compare' | 'proof'
export type QAScopeRequested = 'book' | 'section_then_book'
export type QAScopeUsed = 'section' | 'book'

export interface QAHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface QARequest {
  question: string
  section_id: string | null
  history: QAHistoryMessage[]
}

export interface QACitationItem {
  evidence_id: string
  source_kind: string
  source_id: string
  chapter_id: string | null
  section_id: string | null
  object_type: string | null
  type_zh: string | null
  number: string | null
  title_zh: string | null
  title_en: string | null
  printed_page: number | string | null
  pdf_page: number | null
  source_anchor: string | null
  /** @deprecated Removed from the v2 server DTO; kept only until Task 9 migrates QAPage keys. */
  citation_id?: never
}

export interface QAResponse {
  course_id: string
  book_id: string
  question: string
  answer: string | null
  answer_kind: 'generated' | 'system_notice'
  answer_style: QAAnswerStyle | null
  scope_requested: QAScopeRequested
  scope_used: QAScopeUsed
  insufficient_evidence: boolean
  message: string | null
  citations: QACitationItem[]
}
