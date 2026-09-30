import type { QAResponse } from '../api/types'
import { qaResponseSchema } from '../api/sourceContracts'

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

const isQAResponse = (value: unknown): value is QAResponse => qaResponseSchema.safeParse(value).success

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
      isQAResponse(value.response) &&
      value.content === (value.response.answer ?? value.response.message)
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

/** Preserve the stored v1 shape, but bind each answer to its actual preceding question. */
function validConversation(state: QASessionState, courseId: string): boolean {
  if (!state.route.startsWith('/')) return false
  const route = new URL(state.route, 'https://book.invalid')
  if (route.origin !== 'https://book.invalid' || route.pathname !== `/courses/${encodeURIComponent(courseId)}/qa` ||
    route.hash || [...route.searchParams.keys()].some(key => key !== 'section') ||
    route.searchParams.getAll('section').length > 1 ||
    (route.searchParams.has('section') && !route.searchParams.get('section')?.trim())) return false
  const ids = new Set<string>()
  for (let i = 0; i < state.messages.length; i++) {
    const message = state.messages[i]
    if (ids.has(message.id)) return false
    ids.add(message.id)
    if (message.role === 'assistant') {
      const question = state.messages[i - 1]
      if (!question || question.role !== 'user' || question.content.trim() !== message.response.question ||
        message.response.course_id !== courseId) return false
    }
  }
  return true
}

/** IDs must stay unique even after a reload resets the JavaScript module. */
export function createQAMessageId(role: 'user' | 'assistant', messages: QASessionMessage[]): string {
  const used = new Set(messages.map(message => message.id))
  let sequence = messages.length + 1
  while (used.has(`${role}-${sequence}`)) sequence++
  return `${role}-${sequence}`
}

export interface ActiveQASource { bookId: string; kind: string; sourceId: string }
/** The legacy stored selection has only an ID. Ambiguity must never imply a kind or book. */
export function activeQASource(state: QASessionState | null): ActiveQASource | null {
  if (!state?.activeCitationSourceId) return null
  const identities = new Map<string, ActiveQASource>()
  for (const message of state.messages) {
    if (message.role !== 'assistant') continue
    for (const citation of message.response.citations) {
      if (citation.source_id !== state.activeCitationSourceId) continue
      const identity = { bookId: message.response.book_id, kind: citation.source_kind, sourceId: citation.source_id }
      identities.set(JSON.stringify([identity.bookId, identity.kind, identity.sourceId]), identity)
    }
  }
  return identities.size === 1 ? identities.values().next().value ?? null : null
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
    if (!isQASessionState(value) || !validConversation(value, courseId)) {
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
