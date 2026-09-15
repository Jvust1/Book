/* Acceptance for a packaged Book desktop server. */
const fs = require('node:fs');
const path = require('node:path');
const repo = path.resolve(__dirname, '..');
const { chromium, expect } = require(path.join(repo, 'app/web/node_modules/@playwright/test'));
const base = process.env.BOOK_WEB_BASE_URL || 'http://127.0.0.1:17866';
const output = path.join(repo, '.build/desktop-sync');
fs.mkdirSync(output, { recursive: true });

async function main() {
  if (process.env.BOOK_DESKTOP_TEST_ISOLATED !== '1') {
    throw new Error('Set BOOK_DESKTOP_TEST_ISOLATED=1 and start the server with an isolated BOOK_APP_DATA_DIR');
  }
  const browserPath = process.env.BOOK_BROWSER_PATH;
  const browser = await chromium.launch({
    headless: true,
    ...(browserPath ? { executablePath: browserPath } : {}),
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 840 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(base + '/sync');
    await expect(page.getByRole('heading', { name: '学习进度同步' })).toBeVisible();
    await page.evaluate(async () => {
      const response = await fetch('/api/courses/functional_analysis_course/sections/ch01_s01/study/learn/touch', { method: 'POST' });
      if (!response.ok) throw new Error('Unable to create acceptance progress');
    });

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: '导出学习进度' }).click();
    const download = await downloadPromise;
    const progressPath = path.join(output, 'desktop-progress.json');
    await download.saveAs(progressPath);
    const payload = JSON.parse(fs.readFileSync(progressPath, 'utf8'));
    expect(payload.schema_version).toBe('book_study_sync_v1');
    const target = payload.records.find(record =>
      record.course_id === 'functional_analysis_course'
      && record.section_id === 'ch01_s01'
      && record.mode === 'learn'
    );
    expect(target).toBeDefined();
    expect(target.profile_id).toBeUndefined();

    const future = '2099-01-01T00:00:00+00:00';
    payload.records = [{ ...target, status: 'completed', progress: 100, completed_at: future, last_studied_at: future, updated_at: future }];
    const bytes = Buffer.from(JSON.stringify(payload));
    const input = page.locator('input[type=file]');
    await input.setInputFiles({ name: 'phone-progress.json', mimeType: 'application/json', buffer: bytes });
    await expect(page.getByRole('status')).toContainText('1 条已更新');
    const record = await page.evaluate(async () => (await fetch('/api/study/recent')).json());
    expect(record.status).toBe('completed');

    await input.setInputFiles({ name: 'phone-progress.json', mimeType: 'application/json', buffer: bytes });
    await expect(page.getByRole('status')).toContainText('1 条保持原值');
    expect(errors).toEqual([]);
    await page.screenshot({ path: path.join(output, 'sync-page.png'), fullPage: true });
    console.log('PASS desktop packaged manual progress export/import');
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
