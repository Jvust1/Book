/* Run against an installed debug APK on a disposable Android emulator.
 * Usage: node android-app/tests/smoke_android.cjs emulator-5554
 * Requires npm ci in app/web and Android SDK platform-tools.
 */
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const repo = path.resolve(__dirname, '../..');
const { chromium, expect } = require(path.join(repo, 'app/web/node_modules/@playwright/test'));
const sdk = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT
  || path.join(process.env.LOCALAPPDATA || '', 'Android/Sdk');
const adbPath = path.join(sdk, 'platform-tools', process.platform === 'win32' ? 'adb.exe' : 'adb');
const serial = process.argv[2] || 'emulator-5554';
const output = path.join(repo, '.build/android-smoke');
const origin = 'http://127.0.0.1:8765';
const course = 'functional_analysis_course';
const steps = [];
const errors = [];
const forwards = [];
let browser;
let page;
fs.mkdirSync(output, { recursive: true });
const adb = (...args) => execFileSync(adbPath, ['-s', serial, ...args], { encoding: 'utf8', timeout: 30_000 }).trim();
const passed = name => { steps.push(name); console.log('PASS ' + name); };
async function tapSystem(match) {
  await expect.poll(() => {
    adb('shell', 'uiautomator', 'dump', '/sdcard/book-sync-picker.xml');
    return adb('shell', 'cat', '/sdcard/book-sync-picker.xml');
  }, { timeout: 20_000 }).toMatch(match);
  const xml = adb('shell', 'cat', '/sdcard/book-sync-picker.xml');
  const node = xml.match(/<node[^>]+>/g).find(item => match.test(item));
  const bounds = node.match(/bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"/);
  adb('shell', 'input', 'tap', String((+bounds[1] + +bounds[3]) / 2), String((+bounds[2] + +bounds[4]) / 2));
}

async function connect() {
  const pid = adb('shell', 'pidof', 'com.jvust.book.app');
  if (!/^\d+$/.test(pid)) throw new Error('Book debug APK is not running');
  const port = adb('forward', 'tcp:0', 'localabstract:webview_devtools_remote_' + pid);
  forwards.push(port);
  await expect.poll(async () => {
    try { return (await fetch(`http://127.0.0.1:${port}/json/version`)).status; }
    catch { return 0; }
  }, { timeout: 30_000 }).toBe(200);
  // Android WebView does not expose desktop browser download/context controls.
  browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`, { noDefaults: true });
  page = browser.contexts()[0].pages()[0];
  page.on('pageerror', error => errors.push(error.message));
  page.setDefaultTimeout(20_000);
  await expect.poll(() => page.url(), { timeout: 30_000 }).toContain(origin);
  await page.goto(origin);
  await expect(page.getByRole('link', { name: '进入课程' })).toBeVisible({ timeout: 30_000 });
}

async function api(url, data) {
  return page.evaluate(async ({ url, data }) => {
    const response = await fetch(url, data === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
    return { status: response.status, body: await response.json() };
  }, { url, data });
}

async function main() {
  adb('shell', 'wm', 'user-rotation', 'lock', '0');
  await connect();
  const library = await api('/api/library');
  expect(library.status).toBe(200);
  expect(library.body.courses[0].section_count).toBe(132);
  await page.screenshot({ path: path.join(output, 'library.png') });
  passed('APK startup and bundled library');

  await page.getByRole('link', { name: '进入课程' }).click();
  await page.locator('a[href*="/chapters/"]').first().click();
  await page.locator('a[href*="/sections/"]').first().click();
  await expect(page.getByRole('tab', { name: '学习', exact: true })).toBeVisible();
  const sectionPath = new URL(page.url()).pathname;
  for (const name of ['预习', '学习', '复习', '刷题']) {
    const tab = page.getByRole('tab', { name, exact: true });
    await tab.click();
    await expect(tab).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByText(/学习进度：(进行中|已完成)/)).toBeVisible();
    expect(await page.getByRole('alert').count()).toBe(0);
  }
  passed('Course navigation and all four learning modes');

  await page.getByRole('tab', { name: '学习', exact: true }).click();
  await expect(page.getByText(/学习进度：(进行中|已完成)/)).toBeVisible();
  const complete = page.getByRole('button', { name: '标记完成', exact: true });
  if (await complete.count()) await complete.click();
  await expect(page.getByText('学习进度：已完成')).toBeVisible();
  const recordsBefore = await api(`/api/courses/${course}/study-records`);
  const sectionId = sectionPath.split('/').pop();
  const completedBefore = recordsBefore.body.records.find(row => row.section_id === sectionId && row.mode === 'learn');
  expect(completedBefore.progress).toBe(100);
  await page.reload();
  await expect(page.getByText('学习进度：已完成')).toBeVisible();
  await page.screenshot({ path: path.join(output, 'learning.png') });
  passed('SQLite completion and page refresh');

  await page.locator('a[href*="/sources/"]').first().click();
  await expect(page.getByRole('heading', { name: '教材来源', exact: true })).toBeVisible();
  adb('shell', 'input', 'keyevent', '4');
  await expect.poll(() => new URL(page.url()).pathname).toBe(sectionPath);
  await expect(page.getByText('学习进度：已完成')).toBeVisible();
  passed('Source navigation and Android system back');

  await page.goto(`${origin}/courses/${course}/search`);
  await page.getByRole('searchbox', { name: '教材搜索词' }).fill('Hölder');
  await page.getByRole('button', { name: '搜索', exact: true }).click();
  await expect(page.locator('.search-result-card').first()).toBeVisible();
  await page.getByRole('searchbox', { name: '教材搜索词' }).fill('rotation draft');
  adb('shell', 'wm', 'user-rotation', 'lock', '1');
  await expect.poll(() => page.evaluate(() => innerWidth > innerHeight)).toBe(true);
  await expect(page.getByRole('searchbox', { name: '教材搜索词' })).toHaveValue('rotation draft');
  await page.getByRole('searchbox', { name: '教材搜索词' }).evaluate(input => input.blur());
  adb('shell', 'wm', 'user-rotation', 'lock', '0');
  await expect.poll(() => page.evaluate(() => innerWidth < innerHeight)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  await page.screenshot({ path: path.join(output, 'search.png') });
  passed('Search, rotation draft preservation and mobile layout');

  const invalid = await api(`/api/courses/${course}/qa`, { question: '1/p + 1/q = 1', history: [{ role: 'user', content: 42 }] });
  expect(invalid.status).toBe(400);
  const unavailable = await api(`/api/courses/${course}/qa`, { question: '1/p + 1/q = 1' });
  expect(unavailable.status).toBe(503);
  expect(unavailable.body.error.code).toBe('qa_provider_unconfigured');
  expect((await api('/api/does-not-exist')).status).toBe(404);
  expect(await page.evaluate(async () => (await fetch('/assets/missing.js')).status)).toBe(404);
  expect(await page.evaluate(async () => (await navigator.serviceWorker.getRegistrations()).length)).toBe(0);
  passed('Strict QA validation, honest unconfigured-model state and asset routing');

  await page.goto(`${origin}/sync`);
  await expect(page.getByRole('heading', { name: '学习进度同步' })).toBeVisible();
  const exported = await api('/api/study/export');
  expect(exported.status).toBe(200);
  expect(exported.body.schema_version).toBe('book_study_sync_v1');
  expect(exported.body.records.length).toBeGreaterThan(0);
  expect(exported.body.records[0].profile_id).toBeUndefined();
  const repeatedImport = await api('/api/study/import', exported.body);
  expect(repeatedImport.status).toBe(200);
  expect(repeatedImport.body.imported_count).toBe(0);
  const invalidImport = await api('/api/study/import', { schema_version: 'wrong', records: [] });
  expect(invalidImport.status).toBe(400);
  expect(invalidImport.body.error.code).toBe('invalid_study_sync');

  await page.getByRole('button', { name: '导出学习进度' }).click();
  await tapSystem(/text="(?:SAVE|保存)" resource-id="android:id\/button1"/);
  await expect(page.getByRole('button', { name: '导出学习进度' })).toBeEnabled();
  await expect(page.getByRole('status')).toContainText('已导出');

  await page.getByRole('button', { name: '导入学习进度' }).click();
  await tapSystem(/text="book-study-progress-[^"]+\.json"/);
  await expect(page.getByRole('status')).toContainText('导入完成');
  passed('Manual progress export/import API and Android system pickers');

  await browser.close();
  browser = undefined;
  adb('shell', 'am', 'force-stop', 'com.jvust.book.app');
  adb('shell', 'am', 'start', '-W', '-n', 'com.jvust.book.app/.MainActivity');
  await connect();
  await page.goto(`${origin}${sectionPath}?mode=learn`);
  await expect(page.getByText('学习进度：已完成')).toBeVisible();
  const recordsAfter = await api(`/api/courses/${course}/study-records`);
  const completedAfter = recordsAfter.body.records.find(row => row.section_id === sectionId && row.mode === 'learn');
  expect(completedAfter.completed_at).toBe(completedBefore.completed_at);
  expect(completedAfter.progress).toBe(100);
  passed('Completion survives Android process restart');
  expect(errors).toEqual([]);
  fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify({ serial, steps, errors }, null, 2));
}

main().catch(async error => {
  console.error(error);
  if (page && !page.isClosed()) await page.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {});
  process.exitCode = 1;
}).finally(async () => {
  if (browser) await browser.close();
  for (const port of forwards) adb('forward', '--remove', 'tcp:' + port);
});
