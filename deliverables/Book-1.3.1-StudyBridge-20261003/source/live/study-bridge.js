"use strict";
// Main-process only. No model/TTS, shell, asset loading, or renderer networking.
const http = require("node:http");
const crypto = require("node:crypto");
const { assertTrustedMainFrame } = require("./window-policy.js");
const IDENTIFIER = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$/;
const MAX_BYTES = 32768;
function exact(value, keys) {
  return value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).sort().join("|") === [...keys].sort().join("|");
}
function validId(value) { return typeof value === "string" && IDENTIFIER.test(value); }
function validText(value, max) { return typeof value === "string" && value.trim().length > 0 && value.length <= max && !value.includes("\u0000"); }
function validatePresentation(value, now = Date.now()) {
  if (!exact(value, ["schema", "session_id", "message_id", "decision_id", "producer_session", "progress_sequence", "text", "emotion", "expires_at", "generation"])
      || value.schema !== "mygpt.live2d-presentation.v1"
      || ![value.session_id, value.message_id, value.decision_id, value.producer_session].every(validId)
      || !Number.isSafeInteger(value.progress_sequence) || value.progress_sequence < 1
      || !Number.isSafeInteger(value.generation) || value.generation < 0
      || !validText(value.text, 4000) || !validText(value.emotion, 32)
      || typeof value.expires_at !== "string" || !/T.*(?:Z|[+-]\d\d:\d\d)$/.test(value.expires_at)) throw new Error("INVALID_PRESENTATION");
  const expires = Date.parse(value.expires_at);
  if (!Number.isFinite(expires) || expires <= now || expires - now > 15000) throw new Error("INVALID_LEASE");
  return Object.freeze({ ...value });
}
function parseObject(raw) {
  const parsed = JSON.parse(raw);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("INVALID_OBJECT");
  // All ingress contracts are flat scalars; reject duplicate top-level keys,
  // including escaped spellings, rather than silently accepting the last one.
  let depth = 0; const keys = new Set();
  for (let i = 0; i < raw.length; i += 1) {
    if (raw[i] === '"') {
      const begin = i++;
      while (i < raw.length) { if (raw[i] === "\\") i += 2; else if (raw[i] === '"') break; else i += 1; }
      let next = i + 1; while (/\s/.test(raw[next] || "x")) next += 1;
      if (depth === 1 && raw[next] === ":") { const key = JSON.parse(raw.slice(begin, i + 1)); if (keys.has(key)) throw new Error("DUPLICATE_KEY"); keys.add(key); }
    } else if (raw[i] === "{" || raw[i] === "[") depth += 1;
    else if (raw[i] === "}" || raw[i] === "]") depth -= 1;
  }
  return parsed;
}

function createStudyBridge({ ipcMain, getTarget, token, port = 8767, testMode = false, now = Date.now }) {
  if (typeof token !== "string" || token.length < 32 || token.length > 256 || !/^[\x21-\x7e]+$/.test(token)) throw new Error("LIVE_STUDY_TOKEN_REQUIRED");
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error("INVALID_PORT");
  const auth = Buffer.from("Bearer " + token); const receipts = new Map(); const times = [];
  let generation = 0, current = null, pending = null, reply = null, leaseTimer = null, origin = null;
  const mode = testMode ? "offscreen_test" : "visible";
  function send(target, channel, value) { if (target?.window && !target.window.isDestroyed()) target.window.webContents.send(channel, value); }
  function clearState(advanceGeneration = true) {
    if (advanceGeneration) generation += 1;
    clearTimeout(leaseTimer); leaseTimer = null; reply = null;
    if (current) send(current.target, "live:study-clear", {});
    current = null;
    if (pending) { clearTimeout(pending.timer); pending.resolve({ status: "not_presented", display_ack: false, reason: "invalidated" }); pending = null; }
    return { status: "invalidated", generation };
  }
  function invalidate() { return clearState(true); }
  function isCurrent(value) { return current === value && value.generation === generation && now() < Date.parse(value.message.expires_at); }
  function trusted(event, value) { assertTrustedMainFrame(event, value.target.window, value.target.url); }
  ipcMain.handle("live:study-ack", (event, data) => {
    const active = current;
    if (!active || !isCurrent(active) || !pending || !exact(data, ["nonce", "message_id", "session_id"]) || data.nonce !== active.nonce
        || data.message_id !== active.message.message_id || data.session_id !== active.message.session_id) return false;
    trusted(event, active);
    if (!testMode && (!active.target.window.isVisible() || active.target.window.isMinimized())) return false;
    active.displayed = true;
    const result = { status: "presented", message_id: data.message_id, session_id: data.session_id,
      renderer: "spine-pet-or-live-chat", renderer_mode: mode, display_ack: true, model_called: false };
    clearTimeout(pending.timer); pending.resolve(result); pending = null;
    return true;
  });
  ipcMain.handle("live:study-reply", (event, data) => {
    const active = current;
    if (!active || !isCurrent(active) || !active.displayed || active.replied || reply
        || !exact(data, ["nonce", "message_id", "session_id", "text"]) || data.nonce !== active.nonce
        || data.message_id !== active.message.message_id || data.session_id !== active.message.session_id || !validText(data.text, 2000)) return false;
    trusted(event, active);
    if (!testMode && (!active.target.window.isVisible() || active.target.window.isMinimized())) return false;
    reply = { schema: "mygpt.live-user-reply.v1", request_id: "live-reply-" + crypto.randomBytes(12).toString("hex"),
      session_id: data.session_id, reply_to_message_id: data.message_id, text: data.text,
      captured_at: new Date(now()).toISOString() };
    active.replied = true;
    return true;
  });
  async function present(raw) {
    const message = validatePresentation(raw, now());
    if (message.generation !== generation) return { status: "not_presented", display_ack: false, reason: "stale_generation", generation };
    const fingerprint = crypto.createHash("sha256").update(JSON.stringify(message, Object.keys(message).sort())).digest("hex");
    if (receipts.has(message.message_id)) {
      const receipt = receipts.get(message.message_id);
      if (receipt.fingerprint !== fingerprint) throw new Error("MESSAGE_ID_CONFLICT");
      return { status: "not_presented", display_ack: false, replayed: true, reason: "already_attempted" };
    }
    if (pending) return { status: "not_presented", display_ack: false, reason: "busy" };
    const target = getTarget();
    if (!target?.window || target.window.isDestroyed() || target.window.webContents.isLoading()
        || (!testMode && (!target.window.isVisible() || target.window.isMinimized()))) {
      return { status: "not_presented", display_ack: false, reason: "renderer_unavailable" };
    }
    clearState(false);
    const active = { target, message, fingerprint, generation, nonce: crypto.randomBytes(16).toString("hex"), displayed: false, replied: false };
    current = active;
    const result = await new Promise(resolve => {
      pending = { resolve, timer: setTimeout(() => {
        if (current === active) invalidate();
        resolve({ status: "not_presented", display_ack: false, reason: "renderer_ack_timeout" });
      }, Math.max(1, Math.min(1200, Date.parse(message.expires_at) - now()))) };
      leaseTimer = setTimeout(invalidate, Math.max(1, Date.parse(message.expires_at) - now()));
      send(target, "live:study-present", { ...message, nonce: active.nonce, renderer_mode: mode });
    });
    receipts.set(message.message_id, { fingerprint, result });
    while (receipts.size > 128) receipts.delete(receipts.keys().next().value);
    return result;
  }
  function respond(response, status, body) {
    const bytes = Buffer.from(JSON.stringify(body));
    response.writeHead(status, { "Content-Type": "application/json", "Content-Length": bytes.length, "Cache-Control": "no-store", "Connection": "close" }); response.end(bytes);
  }
  const server = http.createServer(async (request, response) => {
    request.setTimeout(2500, () => request.destroy());
    const supplied = Buffer.from(request.headers.authorization || "");
    const expectedHost = origin?.slice(7);
    if (request.headers.host !== expectedHost || (request.headers.origin && request.headers.origin !== origin)) return respond(response, 403, { error: "invalid_origin_or_host" });
    const rawNames = request.rawHeaders.filter((_, index) => index % 2 === 0).map(name => name.toLowerCase());
    if (["authorization", "host", "content-length", "origin"].some(name => rawNames.filter(value => value === name).length > 1)) return respond(response, 400, { error: "duplicate_header" });
    if (supplied.length !== auth.length || !crypto.timingSafeEqual(supplied, auth)) return respond(response, 401, { error: "unauthorized" });
    const stamp = now(); while (times.length && times[0] < stamp - 60000) times.shift();
    if (times.length >= 240) return respond(response, 429, { error: "rate_limited" }); times.push(stamp);
    if (request.url === "/study/health" && request.method === "GET") return respond(response, 200, { status: "local_live_chat", generation, renderer_mode: mode, has_displayed_message: Boolean(current?.displayed && isCurrent(current)), model_calls: 0, tts_calls: 0, actual_live2d_model_verified: false });
    if (request.method !== "POST" || !["/study/present", "/study/invalidate", "/study/replies/take"].includes(request.url)) return respond(response, 404, { error: "not_found" });
    const length = Number(request.headers["content-length"]);
    if (request.headers["transfer-encoding"] || !Number.isInteger(length) || length < 1 || length > MAX_BYTES) return respond(response, 413, { error: "invalid_body_size" });
    if (request.headers["content-type"]?.split(";")[0] !== "application/json") return respond(response, 415, { error: "invalid_content_type" });
    try {
      const parts = []; let size = 0;
      for await (const chunk of request) { size += chunk.length; if (size > MAX_BYTES) throw new Error("BODY_LIMIT"); parts.push(chunk); }
      if (size !== length) throw new Error("INCOMPLETE_BODY");
      const value = parseObject(Buffer.concat(parts).toString("utf8"));
      if (request.url === "/study/present") {
        const result = await present(value); return respond(response, result.display_ack ? 200 : 409, result);
      }
      if (request.url === "/study/invalidate") {
        if (!exact(value, [])) throw new Error("INVALID_INVALIDATION");
        return respond(response, 200, invalidate());
      }
      if (!exact(value, ["session_id"]) || !validId(value.session_id)) throw new Error("INVALID_SESSION");
      let taken = null;
      if (current && isCurrent(current) && reply?.session_id === value.session_id) { taken = reply; reply = null; }
      return respond(response, 200, { status: taken ? "available" : "unavailable", reply: taken });
    } catch { if (!response.headersSent) respond(response, 400, { error: "invalid_or_expired_study_request" }); }
  });
  server.maxConnections = 16;
  server.requestTimeout = 3000; server.headersTimeout = 3000; server.keepAliveTimeout = 1;
  return {
    async start() { await new Promise((resolve, reject) => { server.once("error", reject); server.listen(port, "127.0.0.1", resolve); }); origin = "http://127.0.0.1:" + server.address().port; return origin; },
    async close() { invalidate(); ipcMain.removeHandler("live:study-ack"); ipcMain.removeHandler("live:study-reply"); server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); },
    invalidate,
    get origin() { return origin; }
  };
}
module.exports = Object.freeze({ createStudyBridge, validatePresentation, parseObject });

