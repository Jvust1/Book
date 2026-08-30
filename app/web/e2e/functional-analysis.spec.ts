import {
  expect,
  test,
  type APIRequestContext,
  type Page,
  type Request,
} from '@playwright/test'

const BASE_URL = 'http://127.0.0.1:5173'
const COURSE_ID = 'functional_analysis_course'
const SECTION_ID = 'ch01_s01'
const COURSE_QA_QUESTION = '1/p + 1/q = 1'
const INSUFFICIENT_QA_QUESTION = 'definitely-no-such-textbook-concept-92831'
const INSUFFICIENT_MESSAGE = '根据当前教材中检索到的内容，暂时无法可靠回答这个问题。'

type ChapterCard = {
  chapter_id: string
}

type SectionCard = {
  section_id: string
  number: string | null
  title_zh: string | null
  title_en: string | null
}

type CourseResponse = {
  course: {
    course_id: string
    chapter_count: number
    section_count: number
  }
  chapters: ChapterCard[]
  section_count: number
}

type ChapterResponse = {
  sections: SectionCard[]
}

type ModeItem = {
  kind: string
  source_id: string
  number: string | null
  title_zh: string | null
  title_en: string | null
  formula: string | null
}

type ModeResponse = {
  items: ModeItem[]
  source_refs: Array<{ kind: string; source_id: string }>
}

type SourceResponse = {
  kind: string
  source_id: string
  printed_page: number | string | null
  pdf_page: number | null
  source_anchor: string | null
}

type SearchResult = {
  source_kind: string
  source_id: string
  object_type: string | null
  title_zh: string | null
}

type SearchResponse = {
  query: string
  result_count: number
  results: SearchResult[]
}

type QACitation = {
  evidence_id: string
  source_kind: string
  source_id: string
  section_id: string | null
  title_zh: string | null
}

type QAResponse = {
  question: string
  answer: string | null
  answer_kind: 'generated' | 'system_notice'
  answer_style: 'brief' | 'explain' | 'compare' | 'proof' | null
  scope_requested: 'book' | 'section_then_book'
  scope_used: 'book' | 'section'
  insufficient_evidence: boolean
  message: string | null
  citations: QACitation[]
}

type QARequestBody = {
  question: string
  section_id: string | null
  history: Array<{ role: 'user' | 'assistant'; content: string }>
}

async function readJson<T>(response: {
  ok(): boolean
  status(): number
  json(): Promise<unknown>
}): Promise<T> {
  expect(response.ok(), `API request failed with HTTP ${response.status()}`).toBe(true)
  return (await response.json()) as T
}

async function askViaApi(
  request: APIRequestContext,
  question: string,
  sectionId: string | null,
): Promise<QAResponse> {
  return readJson<QAResponse>(
    await request.post(`${BASE_URL}/api/courses/${COURSE_ID}/qa`, {
      data: { question, section_id: sectionId, history: [] },
    }),
  )
}

async function sectionLearn(request: APIRequestContext): Promise<ModeResponse> {
  return readJson<ModeResponse>(
    await request.get(
      `${BASE_URL}/api/courses/${COURSE_ID}/sections/${SECTION_ID}/learn`,
    ),
  )
}

function uniqueCandidates(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.map((value) => value?.trim()).filter((value): value is string => Boolean(value)))]
}

async function findSectionSufficientQuestion(request: APIRequestContext): Promise<string> {
  const learn = await sectionLearn(request)
  const candidates = uniqueCandidates(
    learn.items.flatMap((item) => [item.formula, item.title_zh, item.title_en]),
  )

  for (const candidate of candidates.slice(0, 40)) {
    const result = await askViaApi(request, candidate, SECTION_ID)
    if (
      result.answer_kind === 'generated' &&
      result.scope_requested === 'section_then_book' &&
      result.scope_used === 'section' &&
      result.citations.length > 0
    ) {
      return candidate
    }
  }

  throw new Error('No real ch01_s01 question passed the Section evidence gate')
}

async function findSectionFallbackQuestion(request: APIRequestContext): Promise<string> {
  const course = await readJson<CourseResponse>(
    await request.get(`${BASE_URL}/api/courses/${COURSE_ID}`),
  )
  const candidates: string[] = []

  for (const chapter of course.chapters) {
    const payload = await readJson<ChapterResponse>(
      await request.get(
        `${BASE_URL}/api/courses/${COURSE_ID}/chapters/${encodeURIComponent(chapter.chapter_id)}`,
      ),
    )
    for (const section of payload.sections) {
      if (section.section_id === SECTION_ID) continue
      candidates.push(...uniqueCandidates([section.title_zh, section.title_en]))
    }
  }

  for (const candidate of [...new Set(candidates)].slice(0, 80)) {
    const result = await askViaApi(request, candidate, SECTION_ID)
    if (
      result.answer_kind === 'generated' &&
      result.scope_requested === 'section_then_book' &&
      result.scope_used === 'book' &&
      result.citations.length > 0
    ) {
      return candidate
    }
  }

  throw new Error('No real textbook question exercised the Section-to-book fallback')
}

async function openCourseQA(page: Page) {
  await page.goto(`/courses/${COURSE_ID}`)
  await page.getByRole('link', { name: '教材问答' }).click()
  await expect(page).toHaveURL(`${BASE_URL}/courses/${COURSE_ID}/qa`)
  await expect(page.getByRole('heading', { name: '教材问答' })).toBeVisible()
}

async function submitQA(page: Page, question: string) {
  await page.getByRole('textbox', { name: '教材问题' }).fill(question)
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/api/courses/${COURSE_ID}/qa`) &&
      response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: '提问' }).click()
  return readJson<QAResponse>(await responsePromise)
}

function recordBrowserQARequests(page: Page): {
  bodies: QARequestBody[]
  stop: () => void
} {
  const bodies: QARequestBody[] = []
  const listener = (request: Request) => {
    if (
      request.method() !== 'POST' ||
      !request.url().endsWith(`/api/courses/${COURSE_ID}/qa`)
    ) {
      return
    }
    const body = request.postDataJSON() as QARequestBody
    bodies.push(body)
  }
  page.on('request', listener)
  return { bodies, stop: () => page.off('request', listener) }
}

test('real Functional Analysis desktop source round trip', async ({ page, request }) => {
  const course = await readJson<CourseResponse>(
    await request.get(`${BASE_URL}/api/courses/${COURSE_ID}`),
  )
  expect(course.course.course_id).toBe(COURSE_ID)
  expect(course.course.chapter_count).toBe(8)
  expect(course.section_count).toBe(132)
  expect(course.chapters.length).toBeGreaterThan(0)

  const chapter = course.chapters[0]
  const chapterPath = `/courses/${COURSE_ID}/chapters/${encodeURIComponent(chapter.chapter_id)}`
  const chapterPayload = await readJson<ChapterResponse>(
    await request.get(`${BASE_URL}/api${chapterPath}`),
  )
  expect(chapterPayload.sections.some((section) => section.section_id === SECTION_ID)).toBe(true)

  const sectionPath = `/courses/${COURSE_ID}/sections/${SECTION_ID}`
  const learn = await sectionLearn(request)
  const realObject =
    learn.items.find((item) => item.kind === 'object' && item.source_id === 'def_lp') ??
    learn.items.find((item) => item.kind === 'object')
  expect(realObject, 'ch01_s01 learn payload must expose at least one real object').toBeTruthy()
  if (!realObject) return
  expect(
    learn.source_refs.some(
      (ref) => ref.kind === realObject.kind && ref.source_id === realObject.source_id,
    ),
  ).toBe(true)

  const sourcePath = `/courses/${COURSE_ID}/sources/${encodeURIComponent(realObject.kind)}/${encodeURIComponent(realObject.source_id)}`
  const source = await readJson<SourceResponse>(
    await request.get(`${BASE_URL}/api${sourcePath}`),
  )
  expect(source.kind).toBe(realObject.kind)
  expect(source.source_id).toBe(realObject.source_id)

  await page.goto('/')
  await expect(page.getByRole('heading', { name: '教材库' })).toBeVisible()
  await page.getByRole('link', { name: '进入课程' }).click()
  await expect(page).toHaveURL(`${BASE_URL}/courses/${COURSE_ID}`)

  await page.locator(`a[href="${chapterPath}"]`).click()
  await expect(page).toHaveURL(`${BASE_URL}${chapterPath}`)

  await page.locator(`a[href="${sectionPath}"]`).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=learn`)
  await expect(page.getByRole('tab', { name: '学习' })).toHaveAttribute('aria-selected', 'true')

  const sourceLink = page.locator(`a[href="${sourcePath}"]`)
  await expect(sourceLink).toBeVisible()
  await sourceLink.click()
  await expect(page).toHaveURL(`${BASE_URL}${sourcePath}`)
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()
  await expect(page.getByText(`教材页：${source.printed_page ?? '暂缺'}`)).toBeVisible()
  await expect(page.getByText(`PDF 页：${source.pdf_page ?? '暂缺'}`)).toBeVisible()
  await expect(page.getByText(`结构化来源：${realObject.kind}:${realObject.source_id}`)).toBeVisible()
  if (source.source_anchor === null) {
    await expect(page.getByText('教材锚点暂未提供')).toBeVisible()
  } else {
    await expect(page.getByText(source.source_anchor, { exact: true })).toBeVisible()
  }

  await page.getByRole('button', { name: '返回学习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=learn`)

  await page.getByRole('tab', { name: '复习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=review&review_preset=full`)
  await page.getByRole('tab', { name: '刷题' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=practice&practice_kind=all`)
})

test('real Functional Analysis desktop textbook search round trip preserves canonical context', async ({ page, request }) => {
  const query = 'Hölder'
  const search = await readJson<SearchResponse>(
    await request.get(`${BASE_URL}/api/courses/${COURSE_ID}/search?q=${encodeURIComponent(query)}`),
  )
  expect(search.query).toBe(query)
  expect(search.result_count).toBeGreaterThan(0)
  const hit = search.results[0]
  expect(hit.source_kind).toBe('object')
  expect(hit.object_type).toBe('theorem')

  const sourceKey = `${hit.source_kind}:${hit.source_id}`
  const sourcePath = `/courses/${COURSE_ID}/sources/${encodeURIComponent(hit.source_kind)}/${encodeURIComponent(hit.source_id)}`

  await page.goto(`/courses/${COURSE_ID}`)
  await page.getByRole('link', { name: '搜索教材' }).click()
  await expect(page).toHaveURL(`${BASE_URL}/courses/${COURSE_ID}/search`)

  await page.getByRole('searchbox', { name: '教材搜索词' }).fill(query)
  await page.getByRole('button', { name: '搜索' }).click()
  await expect(page).toHaveURL(new RegExp(`/courses/${COURSE_ID}/search\\?q=H%C3%B6lder$`))

  const resultCard = page.locator(`[data-source-key="${sourceKey}"]`)
  await expect(resultCard).toBeVisible()
  if (hit.title_zh) {
    await expect(resultCard.getByRole('heading', { name: hit.title_zh })).toBeVisible()
  }
  await resultCard.getByRole('link', { name: '查看教材来源' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sourcePath}`)
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()
  await expect(page.getByText(`结构化来源：${sourceKey}`)).toBeVisible()
  await expect(page.getByRole('button', { name: '返回搜索' })).toBeVisible()

  const persisted = await page.evaluate((courseId) => {
    const raw = sessionStorage.getItem(`book:search-view:${courseId}`)
    return raw ? (JSON.parse(raw) as Record<string, unknown>) : null
  }, COURSE_ID)
  expect(persisted?.query).toBe(query)
  expect(persisted?.activeSourceKey).toBe(sourceKey)
  expect(persisted).not.toHaveProperty('results')

  await page.getByRole('button', { name: '返回搜索' }).click()
  await expect(page).toHaveURL(new RegExp(`/courses/${COURSE_ID}/search\\?q=H%C3%B6lder$`))
  await expect(page.locator(`[data-source-key="${sourceKey}"]`)).toHaveAttribute('aria-current', 'true')
})

test('real Functional Analysis search distinguishes Chinese hits from normal zero hits', async ({ page }) => {
  await page.goto(`/courses/${COURSE_ID}/search`)
  const input = page.getByRole('searchbox', { name: '教材搜索词' })

  await input.fill('巴拿赫空间')
  await page.getByRole('button', { name: '搜索' }).click()
  await expect(page.locator('[data-source-key]').first()).toBeVisible()
  await expect(page.getByText('未找到匹配教材内容')).toHaveCount(0)

  await input.fill('definitely-no-such-text-92831')
  await page.getByRole('button', { name: '搜索' }).click()
  await expect(page.getByText('未找到匹配教材内容')).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('Section QA source round trip restores verified conversation without provider recall and sends history on follow-up', async ({ page, request }) => {
  const question = await findSectionSufficientQuestion(request)
  const course = await readJson<CourseResponse>(
    await request.get(`${BASE_URL}/api/courses/${COURSE_ID}`),
  )
  const chapter = course.chapters[0]
  const chapterPath = `/courses/${COURSE_ID}/chapters/${encodeURIComponent(chapter.chapter_id)}`
  const sectionPath = `/courses/${COURSE_ID}/sections/${SECTION_ID}`
  const qaPath = `/courses/${COURSE_ID}/qa?section=${SECTION_ID}`
  const recorder = recordBrowserQARequests(page)

  await page.goto('/')
  await page.getByRole('link', { name: '进入课程' }).click()
  await page.locator(`a[href="${chapterPath}"]`).click()
  await page.locator(`a[href="${sectionPath}"]`).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=learn`)
  await page.getByRole('link', { name: '问本节内容' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${qaPath}`)
  await expect(page.getByText('优先本节，必要时扩展到全书')).toBeVisible()

  const first = await submitQA(page, question)
  expect(first.answer_kind).toBe('generated')
  expect(first.scope_requested).toBe('section_then_book')
  expect(first.scope_used).toBe('section')
  expect(first.citations.length).toBeGreaterThan(0)
  expect(first.answer).not.toBeNull()
  await expect(page.getByText('回答依据：当前小节')).toBeVisible()
  await expect(page.getByText(first.answer!, { exact: true })).toBeVisible()
  expect(recorder.bodies).toHaveLength(1)
  expect(recorder.bodies[0]).toEqual({
    question,
    section_id: SECTION_ID,
    history: [],
  })

  const citation = first.citations[0]
  const sourcePath = `/courses/${COURSE_ID}/sources/${encodeURIComponent(citation.source_kind)}/${encodeURIComponent(citation.source_id)}`
  const citationCard = page.locator('.qa-citation-card').first()
  await expect(citationCard.getByRole('link', { name: '查看教材来源' })).toHaveAttribute(
    'href',
    sourcePath,
  )
  await citationCard.getByRole('link', { name: '查看教材来源' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sourcePath}`)
  await expect(page.getByRole('button', { name: '返回问答' })).toBeVisible()

  const persistedOnSource = await page.evaluate((courseId) => {
    const raw = sessionStorage.getItem(`book:qa-session:${courseId}`)
    return raw ? (JSON.parse(raw) as Record<string, unknown>) : null
  }, COURSE_ID)
  expect(persistedOnSource?.activeCitationSourceId).toBe(citation.source_id)
  expect(persistedOnSource?.route).toBe(qaPath)
  expect(JSON.stringify(persistedOnSource)).not.toContain('"prompt"')
  expect(JSON.stringify(persistedOnSource)).not.toContain('"raw_response"')
  expect(recorder.bodies).toHaveLength(1)

  await page.getByRole('button', { name: '返回问答' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${qaPath}`)
  await expect(page.getByText(first.answer!, { exact: true })).toBeVisible()
  await expect(page.locator('.qa-citation-card[aria-current="true"]')).toHaveCount(1)
  expect(recorder.bodies).toHaveLength(1)

  const followUp = await submitQA(page, question)
  expect(followUp.answer_kind).toBe('generated')
  expect(recorder.bodies).toHaveLength(2)
  expect(recorder.bodies[1].history).toEqual([
    { role: 'user', content: question },
    { role: 'assistant', content: first.answer },
  ])
  await expect(page.getByText('AI 生成回答，依据下方教材来源')).toHaveCount(2)
  recorder.stop()
})

test('Course QA uses whole-book scope with real textbook evidence', async ({ page }) => {
  await openCourseQA(page)
  await expect(page.getByText('当前范围：整本教材')).toBeVisible()

  const response = await submitQA(page, COURSE_QA_QUESTION)
  expect(response.answer_kind).toBe('generated')
  expect(response.scope_requested).toBe('book')
  expect(response.scope_used).toBe('book')
  expect(response.citations.length).toBeGreaterThan(0)
  await expect(page.getByText('回答依据：整本教材')).toBeVisible()
  await expect(page.getByText('AI 生成回答，依据下方教材来源')).toBeVisible()
})

test('Section QA visibly falls back to other textbook chapters when local evidence is insufficient', async ({ page, request }) => {
  const fallbackQuestion = await findSectionFallbackQuestion(request)
  await page.goto(`/courses/${COURSE_ID}/qa?section=${SECTION_ID}`)
  await expect(page.getByText('优先本节，必要时扩展到全书')).toBeVisible()

  const response = await submitQA(page, fallbackQuestion)
  expect(response.answer_kind).toBe('generated')
  expect(response.scope_requested).toBe('section_then_book')
  expect(response.scope_used).toBe('book')
  await expect(page.getByText('回答依据：本节 + 教材其他章节')).toBeVisible()
})

test('real Functional Analysis textbook QA treats nonexistent questions as normal insufficient evidence', async ({ page }) => {
  await openCourseQA(page)
  const response = await submitQA(page, INSUFFICIENT_QA_QUESTION)

  expect(response.answer_kind).toBe('system_notice')
  expect(response.insufficient_evidence).toBe(true)
  expect(response.answer).toBeNull()
  expect(response.citations).toEqual([])
  expect(response.message).toBe(INSUFFICIENT_MESSAGE)
  await expect(page.getByText(INSUFFICIENT_MESSAGE, { exact: true })).toBeVisible()
  await expect(page.getByText('AI 生成回答，依据下方教材来源')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('real Functional Analysis narrow Section remains reachable without body overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`/courses/${COURSE_ID}/sections/${SECTION_ID}?mode=learn`)
  await expect(page.getByRole('tab', { name: '学习' })).toHaveAttribute('aria-selected', 'true')

  for (const label of ['预习', '学习', '复习', '刷题']) {
    const tab = page.getByRole('tab', { name: label })
    await expect(tab).toBeVisible()
    await tab.scrollIntoViewIfNeeded()
  }

  const fitsViewport = await page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  )
  expect(fitsViewport).toBe(true)
})

test('real Functional Analysis narrow search and source round trip avoid body overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`/courses/${COURSE_ID}/search?q=H%C3%B6lder`)

  const firstResult = page.locator('[data-source-key]').first()
  await expect(firstResult).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true)

  await firstResult.getByRole('link', { name: '查看教材来源' }).click()
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true)

  await page.getByRole('button', { name: '返回搜索' }).click()
  await expect(page.getByRole('heading', { name: '搜索教材' })).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true)
})

test('real Functional Analysis narrow Section QA and source round trip avoid body overflow', async ({ page, request }) => {
  const question = await findSectionSufficientQuestion(request)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`/courses/${COURSE_ID}/qa?section=${SECTION_ID}`)
  await expect(page.getByText('优先本节，必要时扩展到全书')).toBeVisible()

  const response = await submitQA(page, question)
  expect(response.answer_kind).toBe('generated')
  await expect(page.locator('.qa-citation-card').first()).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true)

  await page.locator('.qa-citation-card').first().getByRole('link', { name: '查看教材来源' }).click()
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true)

  await page.getByRole('button', { name: '返回问答' }).click()
  await expect(page.getByRole('heading', { name: '教材问答' })).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true)
})

test('Phase 1H real Learn presentation stays closed and round trips in Chromium', async ({
  page,
  request,
}) => {
  const learn = await sectionLearn(request)
  const learnPresentation = (learn as ModeResponse & {
    presentation?: {
      mode: string
      groups: Array<{
        id: string
        source_refs: Array<{ kind: string; source_id: string }>
      }>
    }
  }).presentation

  expect(learnPresentation?.mode).toBe('learn')
  expect(learnPresentation).toBeTruthy()
  if (!learnPresentation) return

  const itemKeys = new Set(learn.items.map((item) => item.kind + ':' + item.source_id))
  const groupIds = learnPresentation.groups.map((group) => group.id)
  const order = ['definitions', 'theorem_family', 'formulas', 'examples', 'other_objects', 'figures', 'translations']
  expect(groupIds).toEqual([...groupIds].sort((a, b) => order.indexOf(a) - order.indexOf(b)))

  const presentationRefs = learnPresentation.groups.flatMap((group) => group.source_refs)
  expect(presentationRefs.length).toBeGreaterThan(0)
  for (const ref of presentationRefs) {
    expect(itemKeys.has(ref.kind + ':' + ref.source_id)).toBe(true)
  }

  const sectionPath = '/courses/' + COURSE_ID + '/sections/' + SECTION_ID
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(sectionPath + '?mode=learn')
  await expect(page.getByRole('heading', { name: '学习分组' })).toBeVisible()
  await expect(page.locator('img')).toHaveCount(0)

  const learnSourceLink = page.locator('a[href*="/sources/"]').first()
  await expect(learnSourceLink).toBeVisible()
  await learnSourceLink.click()
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()
  await page.getByRole('button', { name: '返回学习' }).click()
  await expect(page).toHaveURL(BASE_URL + sectionPath + '?mode=learn')

  await page.getByRole('tab', { name: '复习' }).click()
  await expect(page).toHaveURL(BASE_URL + sectionPath + '?mode=review&review_preset=full')
  await expect(page.getByRole('button', { name: '1 分钟' })).toBeVisible()
  await page.getByRole('button', { name: '1 分钟' }).click()
  await expect(page).toHaveURL(BASE_URL + sectionPath + '?mode=review&review_preset=one_minute')
  await page.getByRole('button', { name: '5 分钟' }).click()
  await expect(page).toHaveURL(BASE_URL + sectionPath + '?mode=review&review_preset=five_minute')
  await page.getByRole('button', { name: '完整复习' }).click()
  await expect(page).toHaveURL(BASE_URL + sectionPath + '?mode=review&review_preset=full')

  await page.getByRole('tab', { name: '刷题' }).click()
  await expect(page).toHaveURL(BASE_URL + sectionPath + '?mode=practice&practice_kind=all')
  await expect(page.getByRole('button', { name: '全部' })).toBeVisible()

  const fitsViewport = await page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  )
  expect(fitsViewport).toBe(true)
})
