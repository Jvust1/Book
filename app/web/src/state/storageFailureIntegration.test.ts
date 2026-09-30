import { afterEach, expect, it, vi } from 'vitest'
import { loadQASessionState, saveQASessionState } from './qaSessionState'
import { loadSearchViewState, saveSearchViewState } from './searchViewState'
import { loadSectionViewState, saveSectionViewState } from './sectionViewState'

afterEach(() => vi.restoreAllMocks())
it('keeps view-state reads and writes usable when browser sessionStorage access is blocked', () => {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new DOMException('blocked', 'SecurityError') })
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new DOMException('full', 'QuotaExceededError') })
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => { throw new DOMException('blocked', 'SecurityError') })
  expect(() => loadQASessionState('original_course')).not.toThrow()
  expect(() => loadSearchViewState('original_course')).not.toThrow()
  expect(() => loadSectionViewState('original_course', 'original_section', 'review')).not.toThrow()
  const qa = { route: '/courses/original_course/qa', messages: [{ id: 'u1', role: 'user' as const, content: '原创问题' }],
    scrollY: 1, activeCitationSourceId: null }
  const search = { route: '/courses/original_course/search?q=original', query: 'original', scrollY: 2, activeSourceKey: null }
  const section = { route: '/courses/original_course/sections/original_section?mode=review', scrollY: 3,
    expandedSourceIds: ['original_source'], activeSourceId: 'original_source' }
  expect(() => saveQASessionState('original_course', qa)).not.toThrow()
  expect(() => saveSearchViewState('original_course', search)).not.toThrow()
  expect(() => saveSectionViewState('original_course', 'original_section', 'review', section)).not.toThrow()
  expect(loadQASessionState('original_course')).toEqual(qa)
  expect(loadSearchViewState('original_course')).toEqual(search)
  expect(loadSectionViewState('original_course', 'original_section', 'review')).toEqual(section)
})
