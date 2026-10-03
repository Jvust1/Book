import { expect, test } from '@playwright/test'

const course = 'original_algebra_pilot'
const section = 'original_s01'
const recordsPath = `/api/courses/${course}/study-records`

test('an invalid receipt after a real SQLite commit remains unconfirmed until reload recovers truth', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const before = await (await request.get(recordsPath)).json()
  // Neither of these modes is completed by the chapter pilot. The second one
  // also permits an isolated test retry after the first attempt already committed.
  const mode = (['review', 'preview'] as const).find(candidate => !before.records.some(
    (record: { section_id: string; mode: string; status: string }) =>
      record.section_id === section && record.mode === candidate && record.status === 'completed'))
  expect(mode, 'Restart the temporary original-chapter API before repeating the full pilot').toBeTruthy()
  if (!mode) throw new Error('No fresh original mode remains')
  const completionPath = `/api/courses/${course}/sections/${section}/study/${mode}/complete`
  let completions = 0
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('request', req => { if (req.method() === 'POST' && new URL(req.url()).pathname === completionPath) completions++ })
  await page.route(`**${completionPath}`, async route => {
    const response = await route.fetch() // Real mutation reaches the real SQLite repository.
    expect(response.ok()).toBe(true)
    const body = await response.json()
    expect(body.status).toBe('completed')
    expect(body.progress).toBe(100)
    await route.fulfill({ response, json: { ...body, course_id: 'wrong_course' } })
  })
  await page.goto(`/courses/${course}/sections/${section}?mode=${mode}`)
  await expect(page.getByText('学习进度：进行中', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '标记完成', exact: true }).click()
  await expect(page.getByText('学习内容仍可正常查看。学习进度保存结果尚未确认。', { exact: true })).toBeVisible()
  await expect(page.getByText('上次确认进度：进行中', { exact: true })).toBeVisible()
  await expect(page.getByText('学习进度：已完成', { exact: true })).toHaveCount(0)
  await expect(page.getByText('学习进度暂未保存', { exact: false })).toHaveCount(0)
  expect(completions).toBe(1)
  const stored = (await (await request.get(recordsPath)).json()).records.find(
    (record: { section_id: string; mode: string }) => record.section_id === section && record.mode === mode)
  expect(stored).toMatchObject({ course_id: course, book_id: 'original_algebra_book', status: 'completed', progress: 100 })
  expect(stored.completed_at).toBeTruthy()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: 'pilot-test-results/study-receipt-unconfirmed-narrow.png', fullPage: true })
  await page.unroute(`**${completionPath}`)
  await page.reload()
  await expect(page.getByText('学习进度：已完成', { exact: true })).toBeVisible()
  await expect(page.getByText('学习内容仍可正常查看。学习进度保存结果尚未确认。', { exact: true })).toHaveCount(0)
  expect(completions).toBe(1) // Reload touches the mode normally; it never replays completion.
  const recovered = (await (await request.get(recordsPath)).json()).records.find(
    (record: { section_id: string; mode: string }) => record.section_id === section && record.mode === mode)
  expect(recovered.completed_at).toBe(stored.completed_at)
  expect(recovered.progress).toBe(100)
  const savedViews = await page.evaluate(() => Object.keys(sessionStorage).map(key => [key, sessionStorage.getItem(key)]))
  for (const [key, value] of savedViews) {
    expect(key).not.toMatch(/study[_:-]?(record|progress)/i)
    expect(value).not.toMatch(/"(progress|started_at|completed_at|profile_id)"\s*:/)
  }
  expect(errors).toEqual([])
})
