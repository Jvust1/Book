import type { QACitationItem, QAResponse } from '../api/types'

export type QASessionMessage =
  | { id: string; role: 'user'; content: string }
  | { id: string; role: 'assistant'; content: string; response: QAResponse }

export interface QASessionState {
  route: string
  messages: QASessionMessage[]
  scrollY: number
  activeCitationSourceId: string | null
}

const SESSION_KEYS = ['activeCitationSourceId', 'messages', 'route', 'scrollY'] as const
const USER_MESSAGE_KEYS = ['content', 'id', 'role'] as const
const ASSISTANT_MESSAGE_KEYS = ['content', 'id', 'response', 'role'] as const
const RESPONSE_KEYS = [
  'answer',
  'answer_kind',
  'answer_style',
  'book_id',
  'citations',
  'course_id',
  'insufficient_evidence',
  'message',
  'question',
  'scope_requested',
  'scope_used',
] as const
const CITATION_KEYS = [
  'book_id',
] as const
const V2_CITATION_KEYS = [
  'chapter_id',
  'evidence_id',
  'number',
  'object_type',
  'pdf_page',
  'printed_page',
  'section_id',
  'source_anchor',
  'source_id',
  'source_kind',
  'title_en',
  'title_zh',
  'type_zh',
] as const

export function qaSessionStateKey(courseId: string): string {
  return `book:qa-session:${courseId}`
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value) && typeof value === 'object' && !Array.isArray(value)

const hasExactKeys = (
  value: Record<string, unknown>,
  expected: readonly string[],
): boolean => {
  const actual = Object.keys(value).sort()
  const sortedExpected = [...expected].sort()
  return (
    actual.length === sortedExpected.length &&
    actual.every((key, index) => key === sortedExpected[index])
  )
}

const isNonBlankString = (value: unknown): value is string =>
  typeof value === 'string' && value.trim().length > 0

const isNullableString = (value: unknown): value is string | null =>
  value === null || typeof value === 'string'

const isNullablePage = (value: unknown): value is number | string | null =>
  value === null ||
  typeof value === 'string' ||
  (typeof value === 'number' && Number.isFinite(value))

const isCitation = (value: unknown): value is QACitationItem => {
  if (!isRecord(value) || !hasExactKeys(value, V2_CITATION_KEYS)) return false

  return (
    isNonBlankString(value.evidence_id) &&
    isNonBlankString(value.source_kind) &&
    isNonBlankString(value.source_id) &&
    isNullableString(value.chapter_id) &&
    isNullableString(value.section_id) &&
    isNullableString(value.object_type) &&
    isNullableString(value.type_zh) &&
    isNullableString(value.number) &&
    isNullableString(value.title_zh) &&
    isNullableString(value.title_en) &&
    isNullablePage(value.printed_page) &&
    (value.pdf_page === null ||
      (typeof value.pdf_page === 'number' && Number.isFinite(value.pdf_page))) &&
    isNullableString(value.source_anchor)
  )
}

const isQAResponse = (value: unknown): value is QAResponse => {
  if (!isRecord(value) || !hasExactKeys(value, RESPONSE_KEYS)) return false

  if (
    !isNonBlankString(value.course_id) ||
    !isNonBlankString(value.book_id) ||
    !isNonBlankString(value.question) ||
    (value.answer !== null && typeof value.answer !== 'string') ||
    (value.answer_kind !== 'generated' && value.answer_kind !== 'system_notice') ||
    (value.answer_style !== null &&
      value.answer_style !== 'brief' &&
      value.answer_style !== 'explain' &&
      value.answer_style !== 'compare' &&
      value.answer_style !== 'proof') ||
    (value.scope_requested !== 'book' && value.scope_requested !== 'section_then_book') ||
    (value.scope_used !== 'section' && value.scope_used !== 'book') ||
    typeof value.insufficient_evidence !== 'boolean' ||
    !isNullableString(value.message) ||
    !Array.isArray(value.citations) ||
    !value.citations.every(isCitation)
  ) {
    return false
  }

  if (value.answer_kind === 'generated') {
    return (
      value.insufficient_evidence === false &&
      isNonBlankString(value.answer) &&
      value.answer_style !== null &&
      value.message === null &&
      value.citations.length > 0
    )
  }

  return (
    value.insufficient_evidence === true &&
    value.answer === null &&
    value.answer_style === null &&
    isNonBlankString(value.message) &&
    value.citations.length === 0
  )
}

const isMessage = (value: unknown): value is QASessionMessage => {
  if (!isRecord(value)) return false

  if (value.role === 'user') {
    return (
      hasExactKeys(value, USER_MESSAGE_KEYS) &&
      isNonBlankString(value.id) &&
      isNonBlankString(value.content)
    )
  }

  if (value.role === 'assistant') {
    return (
      hasExactKeys(value, ASSISTANT_MESSAGE_KEYS) &&
      isNonBlankString(value.id) &&
      isNonBlankString(value.content) &&
      isQAResponse(value.response)
    )
  }

  return false
}

const isQASessionState = (value: unknown): value is QASessionState => {
  if (!isRecord(value) || !hasExactKeys(value, SESSION_KEYS)) return false

  return (
    isNonBlankString(value.route) &&
    Array.isArray(value.messages) &&
    value.messages.every(isMessage) &&
    typeof value.scrollY === 'number' &&
    Number.isFinite(value.scrollY) &&
    value.scrollY >= 0 &&
    (value.activeCitationSourceId === null || isNonBlankString(value.activeCitationSourceId))
  )
}

export function saveQASessionState(courseId: string, state: QASessionState): void {
  sessionStorage.setItem(qaSessionStateKey(courseId), JSON.stringify(state))
}

export function loadQASessionState(courseId: string): QASessionState | null {
  const key = qaSessionStateKey(courseId)
  const raw = sessionStorage.getItem(key)
  if (raw === null) return null

  try {
    const value: unknown = JSON.parse(raw)
    if (!isQASessionState(value)) {
      sessionStorage.removeItem(key)
      return null
    }
    return value
  } catch {
    sessionStorage.removeItem(key)
    return null
  }
}

export function clearQASessionState(courseId: string): void {
  sessionStorage.removeItem(qaSessionStateKey(courseId))
}
