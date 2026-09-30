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

export function saveQASessionState(courseId: string, state: QASessionState): void {
  sessionStorage.setItem(qaSessionStateKey(courseId), JSON.stringify(state))
}

export function loadQASessionState(courseId: string): QASessionState | null {
  const key = qaSessionStateKey(courseId)
  const raw = sessionStorage.getItem(key)
  if (raw === null) return null

  try {
    const value: unknown = JSON.parse(raw)
    if (!isQASessionState(value) || value.messages.some(message =>
      message.role === 'assistant' && message.response.course_id !== courseId)) {
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
