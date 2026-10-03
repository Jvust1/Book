import { expect, test } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import JSZip from 'jszip'

test('an explicit original QA export downloads an exact local evidence ZIP without another question', async ({ page }) => {
  const course = 'original_algebra_pilot'
  const question = '倍增规则'
  let questions = 0
  page.on('request', request => {
    if (new URL(request.url()).pathname === `/api/courses/${course}/qa` && request.method() === 'POST') questions++
  })
  await page.goto(`/courses/${course}/qa?section=original_s01`)
  await page.getByRole('textbox', { name: '教材问题', exact: true }).fill(question)
  const answered = page.waitForResponse(response => new URL(response.url()).pathname === `/api/courses/${course}/qa`)
  await page.getByRole('button', { name: '提问', exact: true }).click()
  const response = await (await answered).json()
  expect(response.answer_kind).toBe('generated')
  await expect(page.locator('.qa-answer-card')).toHaveCount(1)
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出本次问答 ZIP', exact: true }).click()
  const artifact = await download
  expect(artifact.suggestedFilename()).toBe('book-qa-evidence.zip')
  expect(await artifact.failure()).toBeNull()
  const zip = await JSZip.loadAsync(await readFile((await artifact.path())!), { checkCRC32: true })
  expect(Object.keys(zip.files).sort()).toEqual(['README.txt', 'answer.txt', 'qa-response.json', 'question.txt'])
  expect(await zip.file('question.txt')!.async('string')).toBe(question)
  expect(await zip.file('answer.txt')!.async('string')).toBe(response.answer)
  expect(JSON.parse(await zip.file('qa-response.json')!.async('string'))).toEqual({ schema_version: 'book.qa-evidence.v1', response })
  expect(response.citations[0]).toMatchObject({ source_id: 'doubling_rule', section_id: 'original_s01' })
  await expect(page.getByRole('status')).toContainText('文件不会自动上传')
  expect(questions).toBe(1)
  const saved = await page.evaluate(courseId => JSON.parse(sessionStorage.getItem(`book:qa-session:${courseId}`)!), course)
  expect(saved.messages.map((message: { role: string }) => message.role)).toEqual(['user', 'assistant'])
  await page.reload()
  await expect(page.locator('.qa-answer-card')).toHaveCount(1)
  expect(questions).toBe(1)
})
