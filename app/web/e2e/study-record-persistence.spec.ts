import { expect, test, type APIRequestContext } from '@playwright/test'

const BASE_URL = 'http://127.0.0.1:5173'
const COURSE_ID = 'functional_analysis_course'
const RESERVED_SECTION_ID = 'ch01_s01'

type ChapterCard = {
  chapter_id: string
}

type SectionCard = {
  section_id: string
}

type CourseResponse = {
  chapters: ChapterCard[]
}

type ChapterResponse = {
  sections: SectionCard[]
}

type StudyRecord = {
  course_id: string
  book_id: string
  section_id: string
  mode: 'preview' | 'learn' | 'review' | 'practice'
  status: 'in_progress' | 'completed'
  progress: 0 | 100
  started_at: string
  last_studied_at: string
  completed_at: string | null
  updated_at: string
}

async function readJson<T>(response: {
  ok(): boolean
  status(): number
  json(): Promise<unknown>
}): Promise<T> {
  expect(response.ok(), `API request failed with HTTP ${response.status()}`).toBe(true)
  return (await response.json()) as T
}

async function chooseIsolatedSection(
  request: APIRequestContext,
  retry: number,
): Promise<string> {
  const course = await readJson<CourseResponse>(
    await request.get(`${BASE_URL}/api/courses/${COURSE_ID}`),
  )

  const candidates: string[] = []
  for (const chapter of course.chapters) {
    const chapterPayload = await readJson<ChapterResponse>(
      await request.get(
        `${BASE_URL}/api/courses/${COURSE_ID}/chapters/${encodeURIComponent(chapter.chapter_id)}`,
      ),
    )
    for (const section of chapterPayload.sections) {
      if (section.section_id !== RESERVED_SECTION_ID) {
        candidates.push(section.section_id)
      }
      if (candidates.length >= 4) break
    }
    if (candidates.length >= 4) break
  }

  expect(candidates.length).toBeGreaterThan(retry)
  return candidates[retry]
}

test('real StudyRecord persists completion, keeps modes independent, and survives source round trip', async ({
  page,
  request,
}, testInfo) => {
  const sectionId = await chooseIsolatedSection(request, testInfo.retry)
  const sectionPath = `/courses/${COURSE_ID}/sections/${encodeURIComponent(sectionId)}`

  await page.goto(`${sectionPath}?mode=preview`)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByRole('tab', { name: '预习' })).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByText('学习进度：进行中')).toBeVisible()

  await page.getByRole('tab', { name: '学习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=learn`)
  await expect(page.getByText('学习进度：进行中')).toBeVisible()

  await page.getByRole('button', { name: '标记完成' }).click()
  await expect(page.getByText('学习进度：已完成')).toBeVisible()
  await expect(page.getByRole('button', { name: '标记完成' })).toHaveCount(0)

  await page.reload()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=learn`)
  await expect(page.getByText('学习进度：已完成')).toBeVisible()

  await page.getByRole('tab', { name: '预习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=preview`)
  await expect(page.getByText('学习进度：进行中')).toBeVisible()
  await expect(page.getByText('学习进度：已完成')).toHaveCount(0)

  const recent = await page.evaluate(async () => {
    const response = await fetch('/api/study/recent')
    if (!response.ok) throw new Error(`recent StudyRecord failed: ${response.status}`)
    return (await response.json()) as StudyRecord | null
  })
  expect(recent).not.toBeNull()
  expect(recent?.course_id).toBe(COURSE_ID)
  expect(recent?.section_id).toBe(sectionId)
  expect(recent?.mode).toBe('preview')
  expect(recent).not.toHaveProperty('profile_id')
  expect(recent).not.toHaveProperty('revision')
  expect(recent).not.toHaveProperty('sync_status')

  const sourceLink = page.locator('a[href*="/sources/"]').first()
  await expect(sourceLink).toBeVisible()
  const sourceHref = await sourceLink.getAttribute('href')
  expect(sourceHref).toBeTruthy()
  await sourceLink.click()
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()
  await page.getByRole('button', { name: '返回学习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=preview`)

  await page.setViewportSize({ width: 390, height: 844 })
  const fitsViewport = await page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  )
  expect(fitsViewport).toBe(true)
})
