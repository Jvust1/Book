import { beforeEach, describe, expect, it } from 'vitest'

import {
  clearSearchViewState,
  loadSearchViewState,
  saveSearchViewState,
  searchStateKey,
} from './searchViewState'

describe('searchViewState', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('round-trips only the short-lived course search return state', () => {
    saveSearchViewState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/search?q=H%C3%B6lder',
      query: 'Hölder',
      scrollY: 640,
      activeSourceKey: 'object:thm_1_1_holder',
    })

    expect(loadSearchViewState('functional_analysis_course')).toEqual({
      route: '/courses/functional_analysis_course/search?q=H%C3%B6lder',
      query: 'Hölder',
      scrollY: 640,
      activeSourceKey: 'object:thm_1_1_holder',
    })

    const persisted = JSON.parse(
      sessionStorage.getItem(searchStateKey('functional_analysis_course')) || '{}',
    ) as Record<string, unknown>
    expect(persisted).not.toHaveProperty('results')
  })

  it('rejects malformed or wrong-shaped state and removes it', () => {
    const key = searchStateKey('functional_analysis_course')
    sessionStorage.setItem(key, '{broken')
    expect(loadSearchViewState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()

    sessionStorage.setItem(
      key,
      JSON.stringify({
        route: '/courses/functional_analysis_course/search?q=Banach',
        query: 'Banach',
        scrollY: 'not-a-number',
        activeSourceKey: 'object:def_banach',
      }),
    )
    expect(loadSearchViewState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()
  })

  it('isolates state by course and supports explicit clearing', () => {
    saveSearchViewState('course_a', {
      route: '/courses/course_a/search?q=A',
      query: 'A',
      scrollY: 1,
      activeSourceKey: null,
    })
    saveSearchViewState('course_b', {
      route: '/courses/course_b/search?q=B',
      query: 'B',
      scrollY: 2,
      activeSourceKey: 'object:b',
    })

    clearSearchViewState('course_a')
    expect(loadSearchViewState('course_a')).toBeNull()
    expect(loadSearchViewState('course_b')?.query).toBe('B')
  })
})
