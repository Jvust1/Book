import type { LearningMode } from '../api/types'

export interface SectionViewState {
  route: string
  scrollY: number
  expandedSourceIds: string[]
  activeSourceId: string | null
}

export function stateKey(
  courseId: string,
  sectionId: string,
  mode: LearningMode,
): string {
  return `book:section-view:${courseId}:${sectionId}:${mode}`
}

const isSectionViewState = (value: unknown): value is SectionViewState => {
  if (!value || typeof value !== 'object') return false
  const row = value as Record<string, unknown>
  return (
    typeof row.route === 'string' &&
    typeof row.scrollY === 'number' &&
    Number.isFinite(row.scrollY) &&
    Array.isArray(row.expandedSourceIds) &&
    row.expandedSourceIds.every((item) => typeof item === 'string') &&
    (row.activeSourceId === null || typeof row.activeSourceId === 'string')
  )
}

export function saveSectionViewState(
  courseId: string,
  sectionId: string,
  mode: LearningMode,
  state: SectionViewState,
): void {
  sessionStorage.setItem(stateKey(courseId, sectionId, mode), JSON.stringify(state))
}

export function loadSectionViewState(
  courseId: string,
  sectionId: string,
  mode: LearningMode,
): SectionViewState | null {
  const key = stateKey(courseId, sectionId, mode)
  const raw = sessionStorage.getItem(key)
  if (raw === null) return null

  try {
    const value: unknown = JSON.parse(raw)
    if (!isSectionViewState(value)) {
      sessionStorage.removeItem(key)
      return null
    }
    return value
  } catch {
    sessionStorage.removeItem(key)
    return null
  }
}

export function clearSectionViewState(
  courseId: string,
  sectionId: string,
  mode: LearningMode,
): void {
  sessionStorage.removeItem(stateKey(courseId, sectionId, mode))
}
