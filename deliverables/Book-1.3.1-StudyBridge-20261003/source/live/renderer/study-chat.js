(() => {
  "use strict";
  if (!window.liveStudy) return;
  const panel = document.createElement("section");
  panel.id = "liveStudyChat"; panel.className = "study-chat"; panel.hidden = true;
  panel.setAttribute("aria-label", "Live 学习聊天");
  const title = document.createElement("div"); title.className = "study-chat-title"; title.textContent = "Live · 学习聊天（文字）";
  const body = document.createElement("p"); body.id = "liveStudyMessage"; body.className = "study-chat-message"; body.setAttribute("role", "status"); body.setAttribute("aria-live", "polite");
  const form = document.createElement("form"); form.className = "study-chat-form";
  const input = document.createElement("textarea"); input.id = "liveStudyReply"; input.maxLength = 2000; input.rows = 2;
  input.placeholder = "回复（当前学习会话）"; input.setAttribute("aria-label", "回复学习伙伴");
  const button = document.createElement("button"); button.id = "liveStudySend"; button.type = "submit"; button.textContent = "发送";
  const status = document.createElement("span"); status.id = "liveStudyReplyStatus"; status.setAttribute("role", "status");
  form.append(input, button); panel.append(title, body, form, status); document.body.append(panel);
  let active = null, generation = 0, expiry = null;
  function clear() { generation += 1; active = null; clearTimeout(expiry); panel.hidden = true; body.textContent = ""; input.value = ""; input.disabled = true; button.disabled = true; status.textContent = ""; }
  function current(value) { return active === value && Date.now() < Date.parse(value.expires_at); }
  window.liveStudy.onClear(clear);
  window.liveStudy.onPresent(async value => {
    clear();
    if (!value || typeof value.text !== "string" || value.text.length > 4000 || Date.parse(value.expires_at) <= Date.now()) return;
    active = value; const expected = generation;
    title.textContent = value.renderer_mode === "offscreen_test" ? "Live · 本地隐藏窗口测试（非真实用户可见）" : "Live · 学习聊天（文字）";
    body.textContent = value.text; panel.hidden = false; input.disabled = false; button.disabled = false;
    expiry = setTimeout(clear, Math.max(1, Date.parse(value.expires_at) - Date.now()));
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const rect = panel.getBoundingClientRect();
    // An older RAF continuation must never clear a newer message after revoke
    // and replacement. Only the still-current callback owns clearing its DOM.
    if (active !== value || expected !== generation) return;
    if (!current(value) || panel.hidden || rect.width <= 0 || rect.height <= 0
        || (document.hidden && value.renderer_mode !== "offscreen_test") || getComputedStyle(panel).display === "none") return clear();
    try {
      const acknowledged = await window.liveStudy.ack({ nonce: value.nonce, message_id: value.message_id, session_id: value.session_id });
      if (!acknowledged && current(value)) clear();
      // Keep existing Spine Talk as animation only; do not invent speech/TTS.
      if (acknowledged && current(value) && document.body.dataset.runtime === "spine") window.liveSpinePet?.playNextTalk?.();
    } catch { if (current(value)) clear(); }
  });
  form.addEventListener("submit", async event => {
    event.preventDefault(); const value = active;
    if (!value || !current(value) || !input.value.trim() || input.disabled) return;
    const text = input.value; input.disabled = true; button.disabled = true;
    try {
      const accepted = await window.liveStudy.reply({ nonce: value.nonce, message_id: value.message_id, session_id: value.session_id, text });
      if (!current(value)) return;
      status.textContent = accepted ? "已交给本机 mygpt；不代表模型已回复" : "当前会话已失效，未发送";
      if (accepted) input.value = "";
    } catch { if (current(value)) status.textContent = "发送未确认；不自动重试"; }
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden && active?.renderer_mode !== "offscreen_test") clear(); });
  window.addEventListener("pagehide", clear);
})();

