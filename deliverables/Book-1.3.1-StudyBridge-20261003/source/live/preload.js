const { contextBridge, ipcRenderer } = require("electron");

const animation = Object.freeze({
  pickModel: () => ipcRenderer.invoke("live:animation-pick-model"),
  pickSdk: () => ipcRenderer.invoke("live:animation-pick-sdk"),
  confirmAuthorization: (payload) => ipcRenderer.invoke("live:animation-confirm-authorization", payload),
  revokeAuthorization: () => ipcRenderer.invoke("live:animation-revoke-authorization"),
  prepare: () => ipcRenderer.invoke("live:animation-prepare"),
  closeSession: () => ipcRenderer.invoke("live:animation-close-session"),
  clear: () => ipcRenderer.invoke("live:animation-clear"),
  status: () => ipcRenderer.invoke("live:animation-status")
});

const pet = Object.freeze({
  showPreview: (payload) => ipcRenderer.invoke("live:pet-show", payload),
  pickSpine2870261303: () => ipcRenderer.invoke("live:pet-spine-pick-2870261303"),
  release: () => ipcRenderer.invoke("live:pet-release"),
  rescue: () => ipcRenderer.invoke("live:pet-rescue"),
  hide: () => ipcRenderer.invoke("live:pet-hide"),
  setClickThrough: (enabled) => ipcRenderer.invoke("live:pet-click-through", enabled),
  status: () => ipcRenderer.invoke("live:pet-status")
});

contextBridge.exposeInMainWorld("liveDesktop", Object.freeze({
  version: "0.1.0",
  platform: process.platform,
  pet,
  animation
}));

// Narrow study-only IPC. Credentials and HTTP stay in the main process.
contextBridge.exposeInMainWorld("liveStudy", Object.freeze({
  onPresent(callback) {
    if (typeof callback !== "function") return;
    const listener = (_event, value) => callback(value);
    ipcRenderer.on("live:study-present", listener);
    return () => ipcRenderer.removeListener("live:study-present", listener);
  },
  onClear(callback) {
    if (typeof callback !== "function") return;
    const listener = () => callback();
    ipcRenderer.on("live:study-clear", listener);
    return () => ipcRenderer.removeListener("live:study-clear", listener);
  },
  ack(value) { return ipcRenderer.invoke("live:study-ack", value); },
  reply(value) { return ipcRenderer.invoke("live:study-reply", value); }
}));
