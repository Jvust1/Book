const { app, BrowserWindow, ipcMain, screen, session, dialog } = require("electron");
const path = require("node:path");
if (process.env.LIVE_STUDY_USER_DATA) app.setPath("userData", path.resolve(process.env.LIVE_STUDY_USER_DATA));
const { validatePreviewPayload } = require("./pet-contract.js");
const { pathToFileURL } = require("node:url");
const { assertTrustedMainFrame, secureLocalWindow } = require("./window-policy.js");
const { PetController } = require("./pet-controller.js");
const { inspectRegisteredSpineDirectory, readRegisteredSpineVisualFile } = require("./spine-package.js");
const { AuthorizedAnimationVault } = require("./authorized-animation-vault.js");
const { AuthorizedAnimationBroker } = require("./authorized-animation-broker.js");
const { buildAuthorizedAnimationRendererBridge } = require("./authorized-animation-renderer-ipc.js");
const MAIN_URL = pathToFileURL(path.join(__dirname, "renderer", "index.html")).href;
const ANIMATION_URL = pathToFileURL(path.join(__dirname, "renderer", "animation-host.html")).href;
const PET_URL = pathToFileURL(path.join(__dirname, "renderer", "pet.html")).href;

const LIVE_STUDY_TEST_MODE = process.env.LIVE_STUDY_TEST_MODE === "1";
let studyBridge = null;
const STARTUP_SMOKE = process.env.LIVE_STARTUP_SMOKE === "1";
const STARTUP_SMOKE_TIMEOUT_MS = 10000;
let mainWindow = null;
let animationWindow = null;
let animationReady = null;
let petWindow = null;
let spinePetSession = null;
const authorizedAnimation = new AuthorizedAnimationVault();
const animationBroker = new AuthorizedAnimationBroker(authorizedAnimation);
const animationRendererBridge = buildAuthorizedAnimationRendererBridge({
  broker: animationBroker,
  getWindow: () => animationWindow,
  expectedUrl: ANIMATION_URL
});
const pets = new PetController({
  createWindow: createPetWindow,
  loadWindow: window => window.loadFile(path.join(__dirname, "renderer", "pet.html")),
  primaryArea: () => screen.getPrimaryDisplay().workArea,
  matchingArea: bounds => screen.getDisplayMatching(bounds).workArea
});

function installStartupSmokeNetworkGuard() {
  session.defaultSession.webRequest.onBeforeRequest(
    { urls: ["http://*/*", "https://*/*", "ws://*/*", "wss://*/*"] },
    (details, callback) => {
      console.error(STARTUP_SMOKE ? "LIVE_STARTUP_SMOKE_NETWORK_ATTEMPT" : "LIVE_NETWORK_BLOCKED");
      callback({ cancel: true });
      if (STARTUP_SMOKE) setImmediate(() => app.exit(2));
    }
  );
}

function armStartupSmoke(window) {
  let settled = false;
  const finish = (code, message) => {
    if (settled) return;
    settled = true;
    clearTimeout(timeout);
    const writer = code === 0 ? console.log : console.error;
    writer(message);
    setImmediate(() => (code === 0 ? app.quit() : app.exit(code)));
  };

  const timeout = setTimeout(
    () => finish(1, "LIVE_STARTUP_SMOKE_TIMEOUT"),
    STARTUP_SMOKE_TIMEOUT_MS
  );

  window.webContents.once("did-fail-load", (_event, errorCode, errorDescription) => {
    finish(1, `LIVE_STARTUP_SMOKE_LOAD_FAILED ${errorCode} ${errorDescription}`);
  });
  window.webContents.once("did-finish-load", () => {
    finish(0, "LIVE_STARTUP_SMOKE_OK");
  });

  return (error) => finish(1, `LIVE_STARTUP_SMOKE_LOAD_REJECTED ${error.message}`);
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1100,
    show: !LIVE_STUDY_TEST_MODE,
    height: 720,
    minWidth: 860,
    minHeight: 560,
    backgroundColor: "#0b1020",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      offscreen: LIVE_STUDY_TEST_MODE,
      backgroundThrottling: !LIVE_STUDY_TEST_MODE,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });

  secureLocalWindow(window);
  const reportLoadFailure = STARTUP_SMOKE ? armStartupSmoke(window) : null;
  window.loadFile(path.join(__dirname, "renderer", "index.html")).catch((error) => {
    if (reportLoadFailure) reportLoadFailure(error);
    else console.error("Live renderer failed to load", error);
  });
  window.on("closed", () => {
    if (mainWindow === window) mainWindow = null;
    pets.release();
    releaseAnimationRenderer();
  });
  window.webContents.on("render-process-gone", () => { pets.release(); releaseAnimationRenderer(); });
  window.webContents.on("did-start-loading", () => { pets.release(); releaseAnimationRenderer(); });
  return window;
}

function createPetWindow() {
  const window = new BrowserWindow({
    width: 360,
    height: 520,
    minWidth: 1,
    minHeight: 1,
    show: false,
    frame: false,
    transparent: true,
    backgroundColor: "#00000000",
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    fullscreenable: false,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, "pet-preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });
  petWindow = window;
  for (const event of ["closed", "hide", "minimize"]) window.on(event, () => studyBridge?.invalidate());
  window.webContents.on("render-process-gone", () => studyBridge?.invalidate());
  window.webContents.on("did-start-loading", () => studyBridge?.invalidate());
  secureLocalWindow(window);
  window.setAlwaysOnTop(true, "floating");
  if (process.platform !== "win32") window.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  window.webContents.on("render-process-gone", () => {
    spinePetSession = null;
    pets.release();
  });
  window.on("closed", () => {
    if (petWindow === window) petWindow = null;
    spinePetSession = null;
  });
  return window;
}

function releaseAnimationRenderer() {
  const window = animationWindow;
  animationWindow = null;
  animationReady = null;
  animationBroker.close();
  if (window && !window.isDestroyed()) window.destroy();
}

async function ensureAnimationWindow() {
  if (animationWindow && !animationWindow.isDestroyed()) {
    await animationReady;
    return animationWindow;
  }
  const window = new BrowserWindow({
    width: 640,
    height: 480,
    minWidth: 520,
    minHeight: 360,
    show: false,
    backgroundColor: "#0b1020",
    webPreferences: {
      preload: path.join(__dirname, "animation-preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });
  animationWindow = window;
  secureLocalWindow(window);
  window.on("closed", () => {
    if (animationWindow === window) {
      animationWindow = null;
      animationReady = null;
      animationBroker.close();
    }
  });
  window.webContents.on("render-process-gone", () => { if (animationWindow === window) releaseAnimationRenderer(); });
  animationReady = window.loadFile(path.join(__dirname, "renderer", "animation-host.html"));
  try {
    await animationReady;
    if (animationWindow === window && !window.isDestroyed()) window.show();
    return window;
  } catch (error) {
    if (animationWindow === window) releaseAnimationRenderer();
    throw error;
  }
}

function assertMainSender(event) {
  assertTrustedMainFrame(event, mainWindow, MAIN_URL);
}

function assertPetSender(event) {
  assertTrustedMainFrame(event, petWindow, PET_URL);
}

function animationStatus(extra = {}) {
  return Object.freeze({ ...authorizedAnimation.status(), rendererSession: animationBroker.status(), ...extra });
}

async function pickSpinePet2870261303() {
  if (!mainWindow || mainWindow.isDestroyed()) throw new Error("MAIN_WINDOW_UNAVAILABLE");
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "閫夋嫨 2870261303 宸茶В鍘嬬洰褰?,
    properties: ["openDirectory", "dontAddToRecent"]
  });
  if (result.canceled || result.filePaths.length !== 1) {
    return Object.freeze({ cancelled: true, sourceId: "2870261303" });
  }
  const inspected = inspectRegisteredSpineDirectory("2870261303", result.filePaths[0]);
  spinePetSession = Object.freeze({
    sourceId: "2870261303",
    root: inspected.root,
    spineVersion: inspected.spineVersion
  });
  const status = await pets.showRuntime(Object.freeze({
    sourceId: "2870261303",
    title: "BlueArchive 路 Hibiki Ouenndann",
    width: 512,
    height: 720,
    scale: 1,
    runtime: "spine",
    spineVersion: inspected.spineVersion,
    entry: inspected.entry,
    atlas: inspected.atlas,
    animationCount: inspected.animationCount,
    audio: false,
    network: false
  }));
  return Object.freeze({ ...status, runtime: "spine", spineVersion: inspected.spineVersion,
    animationCount: inspected.animationCount, audio: false, network: false });
}

async function pickAnimationDirectory(kind) {
  if (!mainWindow || mainWindow.isDestroyed()) throw new Error("MAIN_WINDOW_UNAVAILABLE");
  const result = await dialog.showOpenDialog(mainWindow, {
    title: kind === "model" ? "閫夋嫨宸茶幏鎺堟潈鐨?Live2D 妯″瀷鐩綍" : "閫夋嫨浣犱粠 Live2D 瀹樻柟鍙栧緱鐨?Cubism SDK 鐩綍",
    properties: ["openDirectory", "dontAddToRecent"]
  });
  if (result.canceled || result.filePaths.length !== 1) return animationStatus({ cancelled: true });
  releaseAnimationRenderer();
  if (kind === "model") await authorizedAnimation.selectModel(result.filePaths[0]);
  else await authorizedAnimation.selectSdk(result.filePaths[0]);
  return animationStatus();
}

ipcMain.handle("live:pet-show", async (event, input) => {
  assertMainSender(event);
  spinePetSession = null;
  return pets.show(validatePreviewPayload(input));
});
ipcMain.handle("live:pet-spine-pick-2870261303", async event => {
  assertMainSender(event);
  return pickSpinePet2870261303();
});
ipcMain.handle("live:pet-spine-read", (event, relative) => {
  assertPetSender(event);
  if (!spinePetSession) throw new Error("SPINE_PET_SESSION_NOT_READY");
  const asset = readRegisteredSpineVisualFile(
    spinePetSession.sourceId, spinePetSession.root, relative
  );
  return Object.freeze({
    relative: asset.relative,
    mimeType: asset.mimeType,
    bytes: Uint8Array.from(asset.bytes)
  });
});
ipcMain.handle("live:pet-hide", event => { assertMainSender(event); return pets.hide(); });
ipcMain.handle("live:pet-release", event => {
  assertMainSender(event);
  spinePetSession = null;
  return pets.release();
});
ipcMain.handle("live:pet-rescue", event => { assertMainSender(event); return pets.rescue(); });
ipcMain.handle("live:pet-click-through", (event, enabled) => {
  assertMainSender(event); return pets.setClickThrough(enabled);
});
ipcMain.handle("live:pet-status", event => { assertMainSender(event); return pets.status(); });
ipcMain.handle("live:animation-pick-model", async event => { assertMainSender(event); return pickAnimationDirectory("model"); });
ipcMain.handle("live:animation-pick-sdk", async event => { assertMainSender(event); return pickAnimationDirectory("sdk"); });
ipcMain.handle("live:animation-confirm-authorization", (event, input) => {
  assertMainSender(event);
  releaseAnimationRenderer();
  authorizedAnimation.confirmAuthorization(input);
  return animationStatus();
});
ipcMain.handle("live:animation-revoke-authorization", event => { assertMainSender(event); releaseAnimationRenderer(); authorizedAnimation.revokeAuthorization(); return animationStatus(); });
ipcMain.handle("live:animation-prepare", async event => {
  assertMainSender(event);
  releaseAnimationRenderer();
  animationBroker.open();
  try { await ensureAnimationWindow(); } catch (error) { releaseAnimationRenderer(); throw error; }
  return animationStatus();
});
ipcMain.handle("live:animation-close-session", event => { assertMainSender(event); releaseAnimationRenderer(); return animationStatus(); });
ipcMain.handle("live:animation-clear", event => { assertMainSender(event); releaseAnimationRenderer(); authorizedAnimation.clear(); return animationStatus(); });
ipcMain.handle("live:animation-status", event => { assertMainSender(event); return animationStatus(); });
ipcMain.handle("live:animation-renderer-bootstrap", event => animationRendererBridge.bootstrap(event));
ipcMain.handle("live:animation-renderer-read-model", (event, relative) => animationRendererBridge.readModel(event, relative));
ipcMain.handle("live:animation-renderer-read-core", event => animationRendererBridge.readCore(event));

app.whenReady().then(async () => {
  installStartupSmokeNetworkGuard();
  session.defaultSession.setPermissionRequestHandler((_wc, _permission, callback) => callback(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
  for (const event of ["display-removed", "display-metrics-changed"]) screen.on(event, () => pets.recoverDisplay());
  mainWindow = createWindow();
  if (process.env.LIVE_STUDY_TOKEN) {
    const { createStudyBridge } = require("./study-bridge.js");
    studyBridge = createStudyBridge({ ipcMain,
      getTarget: () => petWindow && !petWindow.isDestroyed() && petWindow.isVisible()
        ? { window: petWindow, url: PET_URL } : { window: mainWindow, url: MAIN_URL },
      token: process.env.LIVE_STUDY_TOKEN, port: Number(process.env.LIVE_STUDY_PORT || 8767), testMode: LIVE_STUDY_TEST_MODE });
    const origin = await studyBridge.start();
    console.log(JSON.stringify({ event: "live_study_listening", origin, renderer_mode: LIVE_STUDY_TEST_MODE ? "offscreen_test" : "visible", model_calls: 0, tts_calls: 0 }));
    for (const event of ["closed", "hide", "minimize"]) mainWindow.on(event, () => studyBridge?.invalidate());
    mainWindow.webContents.on("render-process-gone", () => studyBridge?.invalidate());
    mainWindow.webContents.on("did-start-loading", () => studyBridge?.invalidate());
  }

  if (!STARTUP_SMOKE) {
    app.on("activate", () => {
      if (!mainWindow || mainWindow.isDestroyed()) mainWindow = createWindow();
    });
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => { studyBridge?.close().catch(() => {}); });

