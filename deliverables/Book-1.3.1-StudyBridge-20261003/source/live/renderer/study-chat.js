(() => {
  "use strict";
  if (!window.liveStudy) return;
  const panel = document.createElement("section");
  panel.id = "liveStudyChat"; panel.className = "study-chat"; panel.hidden = true;
  panel.setAttribute("aria-label", "Live 瀛︿範鑱婂ぉ");
  const title = document.createElement("div"); title.className = "study-chat-title"; title.textContent = "Live 路 瀛︿範鑱婂ぉ锛堟枃瀛楋級";
  const body = document.createElement("p"); body.id = "liveStudyMessage"; body.className = "study-chat-message"; body.setAttribute("role", "status"); body.setAttribute("aria-live", "polite");
  const form = document.createElement("form"); form.className = "study-chat-form";
  const input = document.createElement("textarea"); input.id = "liveStudyReply"; input.maxLength = 2000; input.rows = 2;
  input.placeholder = "鍥炲锛堝綋鍓嶅涔犱細璇濓級"; input.setAttribute("aria-label", "鍥炲瀛︿範浼欎即");
  const button = document.createElement("button"); button.id = "liveStudySend"; button.type = "submit"; button.textContent = "鍙戦€?;
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
    title.textContent = value.renderer_mode === "offscreen_test" ? "Live 路 鏈湴闅愯棌绐楀彛娴嬭瘯锛堥潪鐪熷疄鐢ㄦ埛鍙锛? : "Live 路 瀛︿範鑱婂ぉ锛堟枃瀛楋級";
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
      status.textContent = accepted ? "宸蹭氦缁欐湰鏈?mygpt锛涗笉浠ｈ〃妯″瀷宸插洖澶? : "褰撳墠浼氳瘽宸插け鏁堬紝鏈彂閫?;
      if (accepted) input.value = "";
    } catch { if (current(value)) status.textContent = "鍙戦€佹湭纭锛涗笉鑷姩閲嶈瘯"; }
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden && active?.renderer_mode !== "offscreen_test") clear(); });
  window.addEventListener("pagehide", clear);
})();

