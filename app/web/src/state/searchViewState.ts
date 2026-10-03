import { sessionViewStorage } from './sessionViewStorage'
export interface SearchViewState {
  route: string
  query: string
  scrollY: number
  activeSourceKey: string | null
}

export function searchStateKey(courseId: string): string {
  return `book:search-view:${courseId}`
}

const isSearchViewState = (value: unknown): value is SearchViewState => {
  if (!value || typeof value !== 'object') return false
  const row = value as Record<string, unknown>
  return (
    typeof row.route === 'string' &&
    typeof row.query === 'string' &&
    typeof row.scrollY === 'number' &&
    Number.isFinite(row.scrollY) &&
    (row.activeSourceKey === null || typeof row.activeSourceKey === 'string')
  )
}

export function saveSearchViewState(
  courseId: string,
  state: SearchViewState,
): void {
  sessionViewStorage.write(searchStateKey(courseId), JSON.stringify(state))
}

export function loadSearchViewState(courseId: string): SearchViewState | null {
  const key = searchStateKey(courseId)
  const raw = sessionViewStorage.read(key)
  if (raw === null) return null

  try {
    const value: unknown = JSON.parse(raw)
    if (!isSearchViewState(value)) {
      sessionViewStorage.remove(key)
      return null
    }
    return value
  } catch {
    sessionViewStorage.remove(key)
    return null
  }
}

export function clearSearchViewState(courseId: string): void {
  sessionViewStorage.remove(searchStateKey(courseId))
}
