import { afterEach, expect, it, vi } from 'vitest'
import { bookApi } from './client'
import { learningCourse, learningPayload, learningSection, learningSectionId } from '../test/learningEncodingFixtures'
function respond(value: unknown) { vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' } }))) }
afterEach(() => vi.unstubAllGlobals())
for (const [caseId, malformed] of ['\ud800', 'embedded\udfffid'].entries()) {
  it.each(['preview', 'learn', 'review', 'practice'] as const)(`rejects malformed %s item and matching source_refs before links (case ${caseId})`, async mode => {
    respond(learningPayload(mode, malformed))
    await expect(bookApi.getMode(learningCourse, learningSectionId, mode)).rejects.toMatchObject({ code: 'invalid_response' })
    expect(fetch).toHaveBeenCalledOnce()
  })
  it(`rejects a malformed Section chapter return identity (case ${caseId})`, async () => {
    respond({ ...learningSection, chapter_id: malformed })
    await expect(bookApi.getSection(learningCourse, learningSectionId)).rejects.toMatchObject({ code: 'invalid_response' })
  })
}
it.each(['原创 🧮 /?&#%', 'e\u0301%2F'])('preserves exact valid learning identities: %s', async id => {
  const section = { ...learningSection, chapter_id: id }
  respond(section); await expect(bookApi.getSection(learningCourse, learningSectionId)).resolves.toEqual(section)
  const payload = learningPayload('learn', id)
  respond(payload); await expect(bookApi.getMode(learningCourse, learningSectionId, 'learn')).resolves.toEqual(payload)
})
it('retains a Section with no chapter instead of inventing a return identity', async () => {
  const value = { ...learningSection, chapter_id: null }; respond(value)
  await expect(bookApi.getSection(learningCourse, learningSectionId)).resolves.toEqual(value)
})
