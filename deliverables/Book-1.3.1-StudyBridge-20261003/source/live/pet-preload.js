const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("livePet", Object.freeze({
  onPreview(callback) {
    if (typeof callback !== "function") return;
    const listener = (_event, payload) => callback(payload);
    ipcRenderer.on("live:pet-preview", listener);
    return () => ipcRenderer.removeListener("live:pet-preview", listener);
  },
  onSpine(callback) {
    if (typeof callback !== "function") return;
    const listener = (_event, payload) => callback(payload);
    ipcRenderer.on("live:pet-spine", listener);
    return () => ipcRenderer.removeListener("live:pet-spine", listener);
  },
  readSpineAsset(relative) {
    return ipcRenderer.invoke("live:pet-spine-read", relative);
  }
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
