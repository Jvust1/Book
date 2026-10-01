import { afterEach, expect, it, vi } from 'vitest'
import { bookApi } from './client'
import { loadQASessionState, qaSessionStateKey } from '../state/qaSessionState'
import { encodingAnswer, encodingCourse, encodingQuestion, encodingSearch, encodingSource } from '../test/sourceEncodingFixtures'
function respond(value: unknown) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' } })))
}
afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear() })
for (const [caseId, malformed] of ['\ud800', '\udfff', 'prefix\ud800suffix'].entries()) {
  it.each(['search', 'qa', 'source-return', 'source-before', 'source-after'] as const)(`rejects non-encodable response IDs in %s (case ${caseId})`, async scope => {
    if (scope === 'search') {
      respond(encodingSearch(malformed))
      await expect(bookApi.searchCourse(encodingCourse, encodingQuestion)).rejects.toMatchObject({ code: 'invalid_response' })
    } else if (scope === 'qa') {
      respond(encodingAnswer(malformed))
      await expect(bookApi.askCourse(encodingCourse, { question: encodingQuestion, section_id: null, history: [] })).rejects.toMatchObject({ code: 'invalid_response' })
    } else {
      const value = encodingSource()
      if (scope === 'source-return') value.section_id = malformed
      else value[scope === 'source-before' ? 'context_before' : 'context_after'] = [{ kind: 'object', source_id: malformed, type: null, number: null, title_zh: null }]
      respond(value)
      await expect(bookApi.getSource(encodingCourse, 'object', 'original_source')).rejects.toMatchObject({ code: 'invalid_response' })
    }
    expect(fetch).toHaveBeenCalledOnce()
  })
}
it.each(['汉字 🧮 /?&#%', 'e\u0301', 'valid%2Fid'])('preserves valid response IDs exactly: %s', async id => {
  respond(encodingSearch(id)); await expect(bookApi.searchCourse(encodingCourse, encodingQuestion)).resolves.toEqual(encodingSearch(id))
  respond(encodingAnswer(id)); await expect(bookApi.askCourse(encodingCourse, { question: encodingQuestion, section_id: null, history: [] })).resolves.toEqual(encodingAnswer(id))
  const value = { ...encodingSource(), section_id: id }
  respond(value); await expect(bookApi.getSource(encodingCourse, 'object', 'original_source')).resolves.toEqual(value)
})

it.each([false, true])('revalidates restored QA citation identity (valid=%s)', valid => {
  const response = encodingAnswer(valid ? '原创 🧮 ?#%' : '\ud800')
  const key = qaSessionStateKey(encodingCourse)
  const state = { route: `/courses/${encodingCourse}/qa`, scrollY: 0, activeCitationSourceId: null,
    messages: [{ id: 'u1', role: 'user', content: encodingQuestion },
      { id: 'a1', role: 'assistant', content: response.answer, response }] }
  sessionStorage.setItem(key, JSON.stringify(state))
  if (valid) expect(loadQASessionState(encodingCourse)).toEqual(state)
  else { expect(loadQASessionState(encodingCourse)).toBeNull(); expect(sessionStorage.getItem(key)).toBeNull() }
})
