import { expect, test } from '@playwright/test'

const BASE_URL = 'http://127.0.0.1:5173'
const COURSE_ID = 'functional_analysis_course'
const SECTION_ID = 'ch01_s01'

type ChapterCard = {
  chapter_id: string
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
  sections: Array<{ section_id: string }>
}

type ModeItem = {
  kind: string
  source_id: string
}

type ModeResponse = {
  items: ModeItem[]
  source_refs: ModeItem[]
}

type SourceResponse = {
  kind: string
  source_id: string
  printed_page: number | string | null
  pdf_page: number | null
  source_anchor: string | null
}

async function readJson<T>(response: {
  ok(): boolean
  status(): number
  json(): Promise<unknown>
}): Promise<T> {
  expect(response.ok(), `API request failed with HTTP ${response.status()}`).toBe(true)
  return (await response.json()) as T
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
  const learn = await readJson<ModeResponse>(
    await request.get(`${BASE_URL}/api${sectionPath}/learn`),
  )
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
  await expect(page.getByRole('tab', { name: '学习' })).toHaveAttribute(
    'aria-selected',
    'true',
  )

  const sourceLink = page.locator(`a[href="${sourcePath}"]`)
  await expect(sourceLink).toBeVisible()
  await sourceLink.click()
  await expect(page).toHaveURL(`${BASE_URL}${sourcePath}`)
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()
  await expect(page.getByText(`教材页：${source.printed_page ?? '暂缺'}`)).toBeVisible()
  await expect(page.getByText(`PDF 页：${source.pdf_page ?? '暂缺'}`)).toBeVisible()
  await expect(
    page.getByText(`结构化来源：${realObject.kind}:${realObject.source_id}`),
  ).toBeVisible()
  if (source.source_anchor === null) {
    await expect(page.getByText('教材锚点暂未提供')).toBeVisible()
  } else {
    await expect(page.getByText(source.source_anchor, { exact: true })).toBeVisible()
  }

  await page.getByRole('button', { name: '返回学习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=learn`)

  await page.getByRole('tab', { name: '复习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=review`)
  await page.getByRole('tab', { name: '刷题' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=practice`)
})

test('real Functional Analysis narrow Section remains reachable without body overflow', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`/courses/${COURSE_ID}/sections/${SECTION_ID}?mode=learn`)
  await expect(page.getByRole('tab', { name: '学习' })).toHaveAttribute(
    'aria-selected',
    'true',
  )

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
