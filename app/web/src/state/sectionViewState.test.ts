import { beforeEach, describe, expect, it } from 'vitest'

import {
  clearSectionViewState,
  loadSectionViewState,
  saveSectionViewState,
  stateKey,
  type SectionViewState,
} from './sectionViewState'

const STATE: SectionViewState = {
  route: '/courses/functional_analysis_course/sections/ch01_s01?mode=review',
  scrollY: 420,
  expandedSourceIds: ['thm_review'],
  activeSourceId: 'thm_review',
}

describe('sectionViewState', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('uses the exact session namespace and round-trips state', () => {
    expect(stateKey('functional_analysis_course', 'ch01_s01', 'review')).toBe(
      'book:section-view:functional_analysis_course:ch01_s01:review',
    )

    saveSectionViewState('functional_analysis_course', 'ch01_s01', 'review', STATE)

    expect(loadSectionViewState('functional_analysis_course', 'ch01_s01', 'review')).toEqual(
      STATE,
    )
  })

  it('clears exact state and rejects corrupt session JSON', () => {
    const key = stateKey('functional_analysis_course', 'ch01_s01', 'learn')
    sessionStorage.setItem(key, '{broken-json')

    expect(loadSectionViewState('functional_analysis_course', 'ch01_s01', 'learn')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()

    saveSectionViewState('functional_analysis_course', 'ch01_s01', 'review', STATE)
    clearSectionViewState('functional_analysis_course', 'ch01_s01', 'review')
    expect(loadSectionViewState('functional_analysis_course', 'ch01_s01', 'review')).toBeNull()
  })
})
