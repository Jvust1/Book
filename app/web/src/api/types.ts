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
