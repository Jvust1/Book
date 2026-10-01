import { expect, test } from '@playwright/test'

const course = 'original_algebra_pilot'
for (const scope of ['library', 'course', 'chapter'] as const) {
  for (const corruption of ['context', 'unpaired-unicode'] as const) {
    test(`the real original ${scope} catalog fails closed on ${corruption} and recovers with browser navigation`, async ({ page, request }) => {
      await page.setViewportSize({ width: 390, height: 844 })
      const actualCourse = await (await request.get(`/api/courses/${course}`)).json()
      const chapter = actualCourse.chapters[0].chapter_id as string
      const target = scope === 'library' ? '/' : scope === 'course' ? `/courses/${course}` : `/courses/${course}/chapters/${chapter}`
      const apiPath = scope === 'library' ? '/api/library' : `/api${target}`
      const errors: string[] = []
      const writes: string[] = []
      page.on('pageerror', error => errors.push(error.message))
      page.on('request', req => { if (req.method() !== 'GET') writes.push(req.url()) })
      await page.route(`**${apiPath}`, async route => {
        const response = await route.fetch() // The current real DTO is the fixture; only its integrity is changed.
        expect(response.ok()).toBe(true)
        const body = await response.json()
        const corrupted = corruption === 'unpaired-unicode'
          ? scope === 'library' ? { ...body, courses: [{ ...body.courses[0], course_id: '\ud800' }] }
            : scope === 'course' ? { ...body, chapters: [{ ...body.chapters[0], chapter_id: '\udfff' }] }
              : { ...body, sections: [{ ...body.sections[0], section_id: '\ud800' }] }
          : scope === 'library' ? { ...body, courses: null } : scope === 'course'
          ? { ...body, course: { ...body.course, course_id: 'wrong_course' } }
          : { ...body, chapter: { ...body.chapter, chapter_id: 'wrong_chapter' } }
        await route.fulfill({ response, json: corrupted })
      })
      await page.goto(target)
      await expect(page.getByRole('alert')).toBeVisible()
      await expect(page.getByText('教材响应校验失败，请刷新后重试', { exact: true })).toBeVisible()
      await expect(page.getByRole('link', { name: /进入课程|进入章节|进入本节/ })).toHaveCount(0)
      if (scope === 'chapter') await page.screenshot({ path: `pilot-test-results/catalog-${corruption}-rejection-narrow.png`, fullPage: true })
      await page.unroute(`**${apiPath}`)
      await page.reload()
      await expect(page.getByRole('alert')).toHaveCount(0)
      const entryName = scope === 'library' ? '进入课程' : scope === 'course' ? '进入章节' : '进入本节'
      await expect(page.getByRole('link', { name: entryName, exact: true })).toHaveCount(1)
      // Read-only catalog navigation must not touch durable progress. Exercise real
      // browser history without entering a Section (whose normal touch is intentional).
      if (scope !== 'chapter') {
        await page.getByRole('link', { name: entryName, exact: true }).click()
        await expect(page.getByRole('link', { name: scope === 'library' ? '进入章节' : '进入本节', exact: true })).toHaveCount(1)
        await page.goBack()
        await expect(page.getByRole('link', { name: entryName, exact: true })).toHaveCount(1)
        await page.goForward()
        await expect(page.getByRole('alert')).toHaveCount(0)
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
      expect(writes).toEqual([])
      expect(errors).toEqual([])
    })
  }
}
