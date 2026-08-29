import { beforeEach, describe, expect, it } from 'vitest'

import type { QAResponse } from '../api/types'
import {
  clearQASessionState,
  loadQASessionState,
  qaSessionStateKey,
  saveQASessionState,
} from './qaSessionState'

const response: QAResponse = {
  course_id: 'functional_analysis_course',
  book_id: 'stein_shakarchi_functional_analysis_2011',
  question: '为什么要这样定义？',
  answer: '基于教材证据的回答。',
  answer_kind: 'generated',
  answer_style: 'explain',
  scope_requested: 'section_then_book',
  scope_used: 'book',
  insufficient_evidence: false,
  message: null,
  citations: [
    {
      evidence_id: 'E1',
      source_kind: 'object',
      source_id: 'def_fixture',
      chapter_id: 'ch01',
      section_id: 'ch01_s01',
      object_type: 'definition',
      type_zh: '定义',
      number: null,
      title_zh: '测试定义',
      title_en: 'Fixture definition',
      printed_page: 12,
      pdf_page: 31,
      source_anchor: null,
    },
  ],
}

describe('qaSessionState', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('round-trips a course-scoped conversation and verified display response', () => {
    saveQASessionState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/qa?section=ch01_s01',
      messages: [
        { id: 'u1', role: 'user', content: '为什么要这样定义？' },
        { id: 'a1', role: 'assistant', content: '基于教材证据的回答。', response },
      ],
      scrollY: 640,
      activeCitationSourceId: 'def_fixture',
    })

    expect(loadQASessionState('functional_analysis_course')).toEqual({
      route: '/courses/functional_analysis_course/qa?section=ch01_s01',
      messages: [
        { id: 'u1', role: 'user', content: '为什么要这样定义？' },
        { id: 'a1', role: 'assistant', content: '基于教材证据的回答。', response },
      ],
      scrollY: 640,
      activeCitationSourceId: 'def_fixture',
    })

    const raw = sessionStorage.getItem(qaSessionStateKey('functional_analysis_course')) || ''
    expect(raw).not.toMatch(/"evidence"\s*:/)
    expect(raw).not.toMatch(/"BOOK_QA_API_KEY"\s*:/)
    expect(raw).not.toMatch(/"prompt"\s*:/)
    expect(raw).not.toMatch(/"raw_response"\s*:/)
    expect(raw).not.toMatch(/"book_version_id"\s*:/)
    expect(raw).not.toMatch(/"logical_book_id"\s*:/)
    expect(raw).not.toMatch(/"provenance"\s*:/)
    expect(raw).not.toMatch(/"retriever_id"\s*:/)
  })

  it('persists only the frozen qa session and verified response shapes', () => {
    saveQASessionState('functional_analysis_course', {
      route: '/courses/functional_analysis_course/qa?section=ch01_s01',
      messages: [
        { id: 'u1', role: 'user', content: '为什么要这样定义？' },
        { id: 'a1', role: 'assistant', content: '基于教材证据的回答。', response },
      ],
      scrollY: 640,
      activeCitationSourceId: 'def_fixture',
    })

    const persisted = JSON.parse(
      sessionStorage.getItem(qaSessionStateKey('functional_analysis_course')) || '{}',
    ) as Record<string, unknown>
    expect(Object.keys(persisted).sort()).toEqual(
      ['activeCitationSourceId', 'messages', 'route', 'scrollY'].sort(),
    )

    const messages = persisted.messages as Array<Record<string, unknown>>
    const persistedResponse = messages[1].response as Record<string, unknown>
    expect(Object.keys(persistedResponse).sort()).toEqual(
      [
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
      ].sort(),
    )
    const citations = persistedResponse.citations as Array<Record<string, unknown>>
    expect(Object.keys(citations[0]).sort()).toEqual(
      [
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
      ].sort(),
    )
  })

  it('rejects cached qa citations with future book-version provenance fields', () => {
    const key = qaSessionStateKey('functional_analysis_course')
    sessionStorage.setItem(
      key,
      JSON.stringify({
        route: '/courses/functional_analysis_course/qa?section=ch01_s01',
        messages: [
          { id: 'u1', role: 'user', content: '为什么要这样定义？' },
          {
            id: 'a1',
            role: 'assistant',
            content: '基于教材证据的回答。',
            response: {
              ...response,
              citations: [
                {
                  ...response.citations[0],
                  book_version_id: 'stein_shakarchi_functional_analysis_2011@v1',
                },
              ],
            },
          },
        ],
        scrollY: 640,
        activeCitationSourceId: 'def_fixture',
      }),
    )

    expect(loadQASessionState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()
  })

  it('removes corrupt or wrong-shaped session state', () => {
    const key = qaSessionStateKey('functional_analysis_course')

    sessionStorage.setItem(key, '{broken')
    expect(loadQASessionState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()

    sessionStorage.setItem(
      key,
      JSON.stringify({
        route: '/courses/functional_analysis_course/qa',
        messages: [{ id: 'a1', role: 'assistant', content: 'missing response' }],
        scrollY: 10,
        activeCitationSourceId: null,
      }),
    )
    expect(loadQASessionState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()

    sessionStorage.setItem(
      key,
      JSON.stringify({
        route: '/courses/functional_analysis_course/qa',
        messages: [{ id: 'x', role: 'system', content: 'not allowed' }],
        scrollY: 10,
        activeCitationSourceId: null,
      }),
    )
    expect(loadQASessionState('functional_analysis_course')).toBeNull()
    expect(sessionStorage.getItem(key)).toBeNull()
  })

  it('isolates sessions by course and supports explicit clearing', () => {
    saveQASessionState('course_a', {
      route: '/courses/course_a/qa',
      messages: [{ id: 'u1', role: 'user', content: 'A?' }],
      scrollY: 1,
      activeCitationSourceId: null,
    })
    saveQASessionState('course_b', {
      route: '/courses/course_b/qa',
      messages: [{ id: 'u2', role: 'user', content: 'B?' }],
      scrollY: 2,
      activeCitationSourceId: 'source_b',
    })

    clearQASessionState('course_a')
    expect(loadQASessionState('course_a')).toBeNull()
    expect(loadQASessionState('course_b')?.messages[0]).toEqual({
      id: 'u2',
      role: 'user',
      content: 'B?',
    })
  })
})