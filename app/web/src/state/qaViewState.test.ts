import { beforeEach, describe, expect, it } from 'vitest'

import {
  clearQAViewState,
  loadQAViewState,
  qaStateKey,
  saveQAViewState,
} from './qaViewState'

describe('qaViewState', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('round-trips only short-lived QA return context', () => {
    saveQAViewState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/qa',
      question: '什么是巴拿赫空间？',
      scrollY: 560,
      activeCitationKey: 'object:def_banach_space',
    })

    expect(loadQAViewState('functional_analysis_course')).toEqual({
      route: '/courses/functional_analysis_course/qa',
      question: '什么是巴拿赫空间？',
      scrollY: 560,
      activeCitationKey: 'object:def_banach_space',
    })

    const persisted = JSON.parse(
      sessionStorage.getItem(qaStateKey('functional_analysis_course')) || '{}',
    ) as Record<string, unknown>
    expect(persisted).not.toHaveProperty('answer')
    expect(persisted).not.toHaveProperty('citations')
  })

  it('rejects malformed, wrong-shaped, or payload-bearing state and removes it', () => {
    const key = qaStateKey('functional_analysis_course')
    sessionStorage.setItem(key, '{broken')
    expect(loadQAViewState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()

    sessionStorage.setItem(
      key,
      JSON.stringify({
        route: '/courses/functional_analysis_course/qa',
        question: '什么是巴拿赫空间？',
        scrollY: 'not-a-number',
        activeCitationKey: 'object:def_banach_space',
      }),
    )
    expect(loadQAViewState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()

    sessionStorage.setItem(
      key,
      JSON.stringify({
        route: '/courses/functional_analysis_course/qa',
        question: '什么是巴拿赫空间？',
        scrollY: 12,
        activeCitationKey: 'object:def_banach_space',
        answer: '不应持久化',
        citations: [{ source_id: 'def_banach_space' }],
      }),
    )
    expect(loadQAViewState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()
  })

  it('isolates state by course and supports explicit clearing', () => {
    saveQAViewState('course_a', {
      route: '/courses/course_a/qa',
      question: 'A?',
      scrollY: 1,
      activeCitationKey: null,
    })
    saveQAViewState('course_b', {
      route: '/courses/course_b/qa',
      question: 'B?',
      scrollY: 2,
      activeCitationKey: 'object:b',
    })

    clearQAViewState('course_a')
    expect(loadQAViewState('course_a')).toBeNull()
    expect(loadQAViewState('course_b')?.question).toBe('B?')
  })
})
