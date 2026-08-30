import { expect, test } from '@playwright/test'

const BASE_URL = 'http://127.0.0.1:5173'
const COURSE_ID = 'functional_analysis_course'
const SECTION_ID = 'ch01_s01'

type ReviewResponse = {
  presentation: {
    mode: 'review'
    presets: Array<{
      id: 'one_minute' | 'five_minute' | 'full'
      label: string
      source_refs: Array<{ kind: string; source_id: string }>
    }>
  }
}

test('real Review preset URL and source round trip preserve selected preset and reveal state', async ({
  page,
  request,
}) => {
  const reviewResponse = await request.get(
    `${BASE_URL}/api/courses/${COURSE_ID}/sections/${SECTION_ID}/review`,
  )
  expect(reviewResponse.ok()).toBe(true)
  const review = (await reviewResponse.json()) as ReviewResponse
  expect(review.presentation.mode).toBe('review')
  const oneMinute = review.presentation.presets.find(
    (preset) => preset.id === 'one_minute',
  )
  expect(oneMinute?.label).toBe('1 分钟')
  expect(oneMinute?.source_refs.length).toBeGreaterThan(0)
  if (!oneMinute || oneMinute.source_refs.length === 0) return

  const selectedRef = oneMinute.source_refs[0]
  const sectionPath = `/courses/${COURSE_ID}/sections/${SECTION_ID}`
  const selectedUrl = `${BASE_URL}${sectionPath}?mode=review&review_preset=one_minute`
  const sourcePath = `/courses/${COURSE_ID}/sources/${encodeURIComponent(selectedRef.kind)}/${encodeURIComponent(selectedRef.source_id)}`

  await page.goto(`${sectionPath}?mode=review`)
  await expect(page).toHaveURL(
    `${BASE_URL}${sectionPath}?mode=review&review_preset=full`,
  )
  await expect(page.getByRole('button', { name: '完整复习' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )

  await page.getByRole('button', { name: '1 分钟' }).click()
  await expect(page).toHaveURL(selectedUrl)
  await expect(page.getByRole('button', { name: '1 分钟' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )

  const reveal = page.getByRole('button', { name: '显示教材内容' }).first()
  await expect(reveal).toBeVisible()
  await reveal.click()
  await expect(page.getByRole('button', { name: '收起教材内容' }).first()).toBeVisible()

  const sourceLink = page.locator(`a[href="${sourcePath}"]`)
  await expect(sourceLink).toBeVisible()
  await sourceLink.click()
  await expect(page).toHaveURL(`${BASE_URL}${sourcePath}`)
  await expect(page.getByRole('heading', { name: '教材来源' })).toBeVisible()

  await page.getByRole('button', { name: '返回学习' }).click()
  await expect(page).toHaveURL(selectedUrl)
  await expect(page.getByRole('button', { name: '1 分钟' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await expect(page.getByRole('button', { name: '收起教材内容' }).first()).toBeVisible()

  await page.getByRole('tab', { name: '学习' }).click()
  await expect(page).toHaveURL(`${BASE_URL}${sectionPath}?mode=learn`)
})
