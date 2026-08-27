export interface QAViewState {
  route: string
  question: string
  scrollY: number
  activeCitationKey: string | null
}

export function qaStateKey(courseId: string): string {
  return `book:qa-view:${courseId}`
}

const QA_VIEW_KEYS = ['activeCitationKey', 'question', 'route', 'scrollY'] as const

const isQAViewState = (value: unknown): value is QAViewState => {
  if (!value || typeof value !== 'object') return false
  const row = value as Record<string, unknown>
  const keys = Object.keys(row).sort()
  if (
    keys.length !== QA_VIEW_KEYS.length ||
    !keys.every((key, index) => key === QA_VIEW_KEYS[index])
  ) {
    return false
  }

  return (
    typeof row.route === 'string' &&
    typeof row.question === 'string' &&
    typeof row.scrollY === 'number' &&
    Number.isFinite(row.scrollY) &&
    (row.activeCitationKey === null || typeof row.activeCitationKey === 'string')
  )
}

export function saveQAViewState(courseId: string, state: QAViewState): void {
  sessionStorage.setItem(qaStateKey(courseId), JSON.stringify(state))
}

export function loadQAViewState(courseId: string): QAViewState | null {
  const key = qaStateKey(courseId)
  const raw = sessionStorage.getItem(key)
  if (raw === null) return null

  try {
    const value: unknown = JSON.parse(raw)
    if (!isQAViewState(value)) {
      sessionStorage.removeItem(key)
      return null
    }
    return value
  } catch {
    sessionStorage.removeItem(key)
    return null
  }
}

export function clearQAViewState(courseId: string): void {
  sessionStorage.removeItem(qaStateKey(courseId))
}
