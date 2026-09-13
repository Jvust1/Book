/* Real AudioRecord/foreground-service acceptance on a disposable emulator only. */
const { execFileSync } = require('node:child_process');
const fs = require('node:fs'), path = require('node:path');
const repo = path.resolve(__dirname, '../..');
const { chromium, expect } = require(path.join(repo, 'app/web/node_modules/@playwright/test'));
const adbPath = path.join(process.env.LOCALAPPDATA, 'Android/Sdk/platform-tools/adb.exe');
const serial = process.argv[2] || 'emulator-5554';
if (!serial.startsWith('emulator-')) throw new Error('Use a disposable emulator; this test changes app permissions and creates test recordings.');
const adb = (...args) => execFileSync(adbPath, ['-s', serial, ...args], { encoding: 'utf8', timeout: 30000 }).trim();
const output = path.join(repo, '.build/recording-013'); fs.mkdirSync(output, { recursive: true });
const steps = [], errors = [], ports = [];
let browser, page;
const origin = 'http://127.0.0.1:8765';
async function connect() {
  const pid = adb('shell', 'pidof', 'com.jvust.book.app');
  const port = adb('forward', 'tcp:0', 'localabstract:webview_devtools_remote_' + pid); ports.push(port);
  await expect.poll(async () => { try { return (await fetch('http://127.0.0.1:' + port + '/json/version')).status } catch { return 0 } }, { timeout: 30000 }).toBe(200);
  browser = await chromium.connectOverCDP('http://127.0.0.1:' + port, { noDefaults: true });
  page = browser.contexts()[0].pages()[0]; page.setDefaultTimeout(20000);
  page.on('pageerror', error => errors.push(error.message));
  await expect.poll(() => page.url(), { timeout: 30000 }).toContain(origin);
}
async function command(action, args = {}) {
  return page.evaluate(({ action, args }) => new Promise((resolve, reject) => {
    const id = 'test-' + crypto.randomUUID();
    const timer = setTimeout(() => reject(new Error('Native request timeout: ' + action)), 20000);
    const handler = event => {
      if (event.detail.id !== id) return;
      clearTimeout(timer); window.removeEventListener('book-native-response', handler);
      if (event.detail.error) reject(new Error(event.detail.error)); else resolve(event.detail.result);
    };
    window.addEventListener('book-native-response', handler);
    window.BookNative.request(JSON.stringify({ action, ...args, id }));
  }), { action, args });
}
async function tapSystem(match) {
  await expect.poll(() => {
    adb('shell', 'uiautomator', 'dump', '/sdcard/book-013-ui.xml');
    return adb('shell', 'cat', '/sdcard/book-013-ui.xml');
  }, { timeout: 20000 }).toMatch(match);
  const xml = adb('shell', 'cat', '/sdcard/book-013-ui.xml');
  const node = xml.match(/<node[^>]+>/g).find(node => match.test(node));
  const bounds = node.match(/bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"/);
  adb('shell', 'input', 'tap', String((+bounds[1] + +bounds[3]) / 2), String((+bounds[2] + +bounds[4]) / 2));
}
const pass = name => { steps.push(name); console.log('PASS ' + name) };
async function permissionChecks() {
  await browser.close(); browser = undefined;
  adb('shell', 'pm', 'revoke', 'com.jvust.book.app', 'android.permission.RECORD_AUDIO');
  adb('shell', 'am', 'start', '-W', '-n', 'com.jvust.book.app/.MainActivity');
  await connect(); await page.goto(origin + '/recording');
  await page.getByRole('button', { name: '开始录音', exact: true }).click();
  await tapSystem(/resource-id="com.android.permissioncontroller:id\/permission_deny(?:_and_dont_ask_again)?_button"/);
  await expect(page.locator('.recording-error')).toContainText('麦克风权限未开启');
  await page.waitForTimeout(1200);
  await expect(page.locator('.recording-error')).toContainText('麦克风权限未开启');
  expect((await command('state')).status).toBe('idle');
  adb('shell', 'pm', 'grant', 'com.jvust.book.app', 'android.permission.RECORD_AUDIO');
  await page.getByRole('button', { name: '开始录音', exact: true }).click();
  await expect.poll(async () => (await command('state')).durationMs).toBeGreaterThan(500);
  pass('Denied permission remains visible; granting permission allows retry');
  adb('shell', 'cmd', 'statusbar', 'expand-notifications');
  await tapSystem(/text="暂停"/);
  await expect.poll(async () => (await command('state')).status).toBe('paused');
  await tapSystem(/text="继续"/);
  await expect.poll(async () => (await command('state')).status).toBe('recording');
  await tapSystem(/text="停止并保存"/);
  adb('shell', 'cmd', 'statusbar', 'collapse');
  await expect.poll(async () => (await command('state')).status).toBe('idle');
  pass('Notification actions pause, resume, and stop/save the live recording');
}
async function main() {
  await connect(); await page.goto(origin + '/recording');
  if (process.argv.includes('--permissions-only')) {
    await permissionChecks();
    expect(errors).toEqual([]);
    fs.writeFileSync(path.join(output, 'permissions-result.json'), JSON.stringify({ serial, steps, errors }, null, 2));
    return;
  }

  await expect(page.getByRole('heading', { name: '课堂录音', exact: true })).toBeVisible();
  const old = await command('list');
  const name = '录音验收-' + Date.now();
  await page.getByLabel('录音名称', { exact: true }).fill(name);
  await page.getByRole('button', { name: '开始录音', exact: true }).click();
  // If permission was already granted by a previous run, skip the permission sheet.
  if ((await command('state')).status === 'idle') {
    await tapSystem(/resource-id="com.android.permissioncontroller:id\/permission_allow_foreground_only_button"/);
  }
  try {
    const permission = adb('shell', 'dumpsys', 'activity', 'activities');
    if (permission.includes('GrantPermissionsActivity')) await tapSystem(/resource-id="com.android.permissioncontroller:id\/permission_allow_button"/);
  } catch {}
  await expect.poll(async () => (await command('state')).status).toBe('recording');
  await expect.poll(async () => (await command('state')).durationMs, { timeout: 10000 }).toBeGreaterThan(1200);
  pass('User-initiated microphone permission and real AudioRecord capture');
  await page.getByRole('button', { name: '暂停录音', exact: true }).click();
  await expect.poll(async () => (await command('state')).status).toBe('paused');
  const paused = await command('state');
  await new Promise(resolve => setTimeout(resolve, 1200));
  expect((await command('state')).durationMs).toBe(paused.durationMs);
  await page.getByRole('button', { name: '继续录音' }).click();
  await expect.poll(async () => (await command('state')).durationMs).toBeGreaterThan(paused.durationMs + 500);
  pass('Pause excludes elapsed time; resume appends to the same recording');
  for (let i = 0; i < 8; i++) { await command('pause'); await command('resume'); }
  await expect.poll(async () => (await command('state')).durationMs).toBeGreaterThan(paused.durationMs + 1000);
  pass('Rapid pause/resume does not confuse an interrupted AudioRecord read');
  await page.getByRole('link', { name: '教材库', exact: true }).click();
  await expect(page.locator('.ongoing-recording')).toBeVisible();
  const beforeBackground = (await command('state')).durationMs;
  adb('shell', 'input', 'keyevent', '3');
  adb('shell', 'input', 'keyevent', '223');
  await new Promise(resolve => setTimeout(resolve, 1800));
  adb('shell', 'input', 'keyevent', '224'); adb('shell', 'wm', 'dismiss-keyguard');
  adb('shell', 'am', 'start', '-W', '-n', 'com.jvust.book.app/.MainActivity');
  expect((await command('state')).durationMs).toBeGreaterThan(beforeBackground + 1000);
  expect(adb('shell', 'dumpsys', 'activity', 'services', 'com.jvust.book.app')).toContain('isForeground=true');
  pass('Page navigation, HOME and lock screen retain foreground recording');
  await page.goto(origin + '/recording');
  await expect(page.getByRole('button', { name: '停止并保存' })).toBeVisible();
  await page.screenshot({ path: path.join(output, 'recording-active.png'), fullPage: false });
  await page.getByRole('button', { name: '停止并保存' }).click();
  await expect.poll(async () => (await command('state')).status).toBe('idle');
  const items = await command('list'), item = items.find(row => row.name === name);
  expect(items.length).toBe(old.length + 1); expect(item.size).toBeGreaterThan(32000);
  const data = await page.evaluate(async id => {
    const res = await fetch('/__recordings/' + id), b = await res.arrayBuffer(), view = new DataView(b);
    const range = await fetch('/__recordings/' + id, { headers: { Range: 'bytes=44-99' } });
    return { status: res.status, length: b.byteLength, riff: new TextDecoder().decode(b.slice(0, 4)),
      dataLength: view.getUint32(40, true), rangeStatus: range.status, rangeSize: (await range.arrayBuffer()).byteLength };
  }, item.id);
  expect(data).toEqual({ status: 200, length: item.size, riff: 'RIFF', dataLength: item.size - 44, rangeStatus: 206, rangeSize: 56 });
  const card = page.locator('.recording-item').filter({ has: page.getByRole('heading', { name, exact: true }) });
  await expect(card).toBeVisible();
  const audio = card.locator('audio');
  await audio.evaluate(audio => audio.play());
  await expect.poll(() => audio.evaluate(audio => audio.currentTime)).toBeGreaterThan(.2);
  await card.getByRole('combobox').selectOption('1.5');
  expect(await audio.evaluate(audio => audio.playbackRate)).toBe(1.5);
  await audio.evaluate(audio => { audio.pause(); audio.currentTime = 1 });
  await expect.poll(() => audio.evaluate(audio => audio.currentTime)).toBeGreaterThan(.9);
  pass('Saved WAV length/header, HTTP Range seeking, playback and playback speed');
  await card.getByRole('button', { name: '重命名' }).click();
  await card.getByLabel('新的录音名称').fill(name + '-已命名');
  await card.getByRole('button', { name: '保存名称' }).click();
  const renamed = page.locator('.recording-item').filter({ has: page.getByRole('heading', { name: name + '-已命名', exact: true }) });
  await expect(renamed).toBeVisible();
  await renamed.getByRole('button', { name: '归档', exact: true }).click();
  await expect(renamed).toHaveCount(0);
  await page.getByRole('button', { name: '查看归档' }).click();
  await expect(renamed).toBeVisible(); await renamed.getByRole('button', { name: '恢复到列表' }).click();
  await page.getByRole('button', { name: '返回录音列表' }).click();
  pass('Rename, reversible archive and restore');
  await renamed.getByRole('button', { name: '导出音频' }).click();
  await tapSystem(/text="SAVE"[^>]+resource-id="android:id\/button1"/);
  await expect(renamed.getByText('已导出录音', { exact: true })).toBeVisible();
  await renamed.getByRole('button', { name: '分享', exact: true }).click();
  await expect.poll(() => adb('shell', 'dumpsys', 'activity', 'activities')).toContain('ChooserActivity');
  adb('shell', 'input', 'keyevent', '4');
  pass('Android document export and temporary-grant share chooser');
  await page.screenshot({ path: path.join(output, 'recordings.png'), fullPage: false });
  const interruptedName = '恢复验收-' + Date.now();
  await command('start', { name: interruptedName });
  await expect.poll(async () => (await command('state')).durationMs).toBeGreaterThan(1200);
  await browser.close(); browser = undefined;
  adb('shell', 'am', 'force-stop', 'com.jvust.book.app');
  adb('shell', 'am', 'start', '-W', '-n', 'com.jvust.book.app/.MainActivity');
  await connect(); await page.goto(origin + '/recording');
  const recovered = (await command('list')).find(row => row.name === interruptedName);
  expect(recovered.interrupted).toBe(true); expect(recovered.size).toBeGreaterThan(32000);
  await expect(page.getByText('这段录音曾中断，已恢复保存到本机的部分。').first()).toBeVisible();
  pass('Force-stop recovery retains PCM bytes and marks interruption honestly');
  const legacyName = 'legacy-export-' + Date.now();
  const fixture = fs.readFileSync(path.join(repo, '.build/web-013/test-recording.webm'));
  await page.evaluate(({ name, bytes }) => new Promise((resolve, reject) => {
    const open = indexedDB.open('book-recordings', 2);
    open.onerror = () => reject(open.error);
    open.onsuccess = () => {
      const db = open.result, tx = db.transaction('recordings', 'readwrite');
      const blob = new Blob([Uint8Array.from(atob(bytes), c => c.charCodeAt(0))], { type: 'audio/webm' });
      tx.objectStore('recordings').put({ id: name, name, createdAt: Date.now(), mimeType: blob.type, blob });
      tx.oncomplete = () => { db.close(); resolve(); }; tx.onabort = () => reject(tx.error);
    };
  }), { name: legacyName, bytes: fixture.toString('base64') });
  await page.reload();
  const legacy = page.locator('.recording-item').filter({ has: page.getByRole('heading', { name: legacyName, exact: true }) });
  await legacy.getByRole('button', { name: '导出音频' }).click();
  await tapSystem(/text="SAVE"[^>]+resource-id="android:id\/button1"/);
  await expect(legacy.getByText('已导出录音', { exact: true })).toBeVisible();
  expect(Number(adb('shell', 'stat', '-c', '%s', '/sdcard/Download/' + legacyName + '.webm'))).toBe(fixture.length);
  pass('Legacy IndexedDB WebM exports through Android SAF with exact byte length');
  await permissionChecks();
  expect(errors).toEqual([]);
  fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify({ serial, steps, errors }, null, 2));
}
main().catch(async error => {
  console.error(error);
  if (page && !page.isClosed()) await page.screenshot({ path: path.join(output, 'failure.png'), timeout: 5000 }).catch(() => {});
  process.exitCode = 1;
}).finally(async () => {
  if (browser) await browser.close();
  for (const port of ports) adb('forward', '--remove', 'tcp:' + port);
});
