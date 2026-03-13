// assets/app.js
const AUTH_KEY = "skinapp_auth";
const RESULT_KEY = "skinapp_result";
const DEV_FORCE_MOCK = false; // 需要時可改 true，強制用 mock

export function toast(msg) {
  const el = document.getElementById("toast");
  if (!el) return alert(msg);
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2400);
}

// ---- Safe fetch helpers (不讓頁面因為 JSON 解析失敗而爆炸) ----
async function safeText(res) {
  try { return await res.text(); } catch { return ""; }
}

export async function safeJsonFetch(url, options = {}, fallback = null) {
  try {
    const res = await fetch(url, { cache: "no-store", ...options });
    const text = await safeText(res);

    // PHP 沒跑 or 回 HTML 時，通常會是 "<" 開頭
    if (text.trim().startsWith("<")) {
      return { ok: false, status: res.status, isHtml: true, data: fallback, raw: text };
    }

    const data = text ? JSON.parse(text) : fallback;
    return { ok: res.ok, status: res.status, data, raw: text };
  } catch (err) {
    return { ok: false, status: 0, error: err, data: fallback, raw: "" };
  }
}

// ---- Backend availability detection ----
async function backendAvailable() {
  if (DEV_FORCE_MOCK) return false;

  // 用 me.php 探測（正式後端應回 JSON；沒跑 PHP 會回 "<?php" or HTML）
  const r = await safeJsonFetch("./api/me.php", {}, null);
  if (r.ok && r.data && typeof r.data === "object") return true;

  // 若是 isHtml 幾乎肯定是靜態伺服器沒跑 PHP
  if (r.isHtml) return false;

  // 其他狀況也視為不可用（例如 404）
  return false;
}

// ---- Auth (前端版；正式可換成後端 session) ----
export function isLoggedIn() {
  return localStorage.getItem(AUTH_KEY) === "1";
}
export function setLoggedIn(v) {
  localStorage.setItem(AUTH_KEY, v ? "1" : "0");
}

export async function requireLogin({ silent = false } = {}) {
  // 若前端已登入，直接放行
  if (isLoggedIn()) return true;

  // 若後端可用，問後端是否已登入（session）
  if (await backendAvailable()) {
    const me = await safeJsonFetch("./api/me.php", {}, { ok: false });
    if (me.ok && me.data?.ok) {
      setLoggedIn(true);
      return true;
    }
  }

  if (!silent) {
    if (window.APP_SINGLE) {
      location.hash = "#login";
    } else {
      location.href = "login.html";
    }
  }
  return false;
}

export async function doLogin(username, password) {
  // 後端可用 → 打真 API
  if (await backendAvailable()) {
    const body = new FormData();
    body.append("username", username);
    body.append("password", password);

    const r = await safeJsonFetch("./api/login.php", { method: "POST", body }, { ok: false });
    if (r.ok && r.data?.ok) {
      setLoggedIn(true);
      return { ok: true };
    }
    return { ok: false, message: r.data?.message || "登入失敗" };
  }

  // 後端不可用 → mock 登入（開發用）
  if (username.trim() && password.trim()) {
    setLoggedIn(true);
    return { ok: true, mock: true };
  }
  return { ok: false, message: "請輸入帳號密碼" };
}

export function logout() {
  setLoggedIn(false);
  localStorage.removeItem(RESULT_KEY);
  if (window.APP_SINGLE) {
    location.hash = "#home";
  } else {
    location.href = "index.html";
  }
}

// ---- Result storage ----
export function saveResult(payload) {
  localStorage.setItem(RESULT_KEY, JSON.stringify(payload));
}
export function loadResult() {
  try {
    const raw = localStorage.getItem(RESULT_KEY) || localStorage.getItem("result");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

// ---- Analyze API (真後端或 mock) ----
function mockAnalyzePayload() {
  // 你可以之後用真的 AI 分析替換
  return {
    ok: true,
    overall: 82,
    photo_url: null,
    metrics: {
      hydration: 76,
      oil: 42,
      redness: 28,
      pores: 55,
      pigmentation: 36,
      texture: 61
    },
    tips: [
      "保濕：晚間加強保濕精華，白天使用含玻尿酸乳液。",
      "泛紅：避免過熱水洗臉，降低刺激性保養。",
      "毛孔：每週 1–2 次溫和去角質，注意防曬。"
    ]
  };
}

export async function analyzePhoto(blob) {
  // 後端可用 → 真上傳
  if (await backendAvailable()) {
    const form = new FormData();
    form.append("photo", blob, "capture.jpg");

    const res = await fetch("./api/analyze.php", { method: "POST", body: form });
    const text = await safeText(res);

    if (text.trim().startsWith("<")) {
      return { ok: false, message: "後端回傳非 JSON（請確認 PHP/路由）" };
    }
    const data = text ? JSON.parse(text) : null;
    return data || { ok: false, message: "後端無資料" };
  }

  // 後端不可用 → mock
  await new Promise(r => setTimeout(r, 650)); // 假裝分析時間
  return mockAnalyzePayload();
}

// ---- Simple charts ----
export function drawBarChart(canvas, valuesObj) {
  const ctx = canvas.getContext("2d");
  const entries = Object.entries(valuesObj);
  const w = canvas.width, h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padding = 18;
  const barGap = 10;
  const barH = Math.floor((h - padding * 2 - barGap * (entries.length - 1)) / entries.length);
  const max = 100;

  // axis bg
  ctx.globalAlpha = 0.16;
  ctx.fillRect(padding, padding, w - padding * 2, h - padding * 2);
  ctx.globalAlpha = 1;

  ctx.font = "12px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif";
  ctx.textBaseline = "middle";

  entries.forEach(([k, v], i) => {
    const y = padding + i * (barH + barGap);
    const x0 = padding + 110;
    const trackW = w - padding - x0;

    // label
    ctx.fillStyle = "rgba(255,255,255,.78)";
    ctx.fillText(k, padding + 6, y + barH / 2);

    // track
    ctx.fillStyle = "rgba(0,0,0,.22)";
    ctx.fillRect(x0, y, trackW, barH);

    // bar
    const bw = Math.max(0, Math.min(trackW, (v / max) * trackW));
    ctx.fillStyle = "rgba(242, 216, 140, .92)"; // 香檳金
    ctx.fillRect(x0, y, bw, barH);

    // value
    ctx.fillStyle = "rgba(255,255,255,.9)";
    ctx.fillText(String(v), x0 + trackW + 8, y + barH / 2);
  });
}

export function drawRadar(canvas, valuesObj) {
  const ctx = canvas.getContext("2d");
  const keys = Object.keys(valuesObj);
  const vals = keys.map(k => valuesObj[k]);

  const w = canvas.width, h = canvas.height;
  const cx = w / 2, cy = h / 2;
  const r = Math.min(w, h) * 0.34;

  ctx.clearRect(0, 0, w, h);
  ctx.translate(0.5, 0.5);

  const levels = 5;

  // grid - 專業高級灰配色
  for (let lv = 1; lv <= levels; lv++) {
    const rr = (r * lv) / levels;
    ctx.beginPath();
    keys.forEach((_, i) => {
      const ang = (Math.PI * 2 * i) / keys.length - Math.PI / 2;
      const x = cx + Math.cos(ang) * rr;
      const y = cy + Math.sin(ang) * rr;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.strokeStyle = "rgba(160, 174, 192, .25)"; // 淺灰藍框線
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // axis + labels
  ctx.font = "13px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif";
  ctx.fillStyle = "rgba(45, 55, 72, .85)"; // 深灰藍文字
  keys.forEach((k, i) => {
    const ang = (Math.PI * 2 * i) / keys.length - Math.PI / 2;
    const x = cx + Math.cos(ang) * (r + 18);
    const y = cy + Math.sin(ang) * (r + 18);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(ang) * r, cy + Math.sin(ang) * r);
    ctx.strokeStyle = "rgba(160, 174, 192, .20)"; // 淺灰藍軸線
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillText(k, x - 18, y);
  });

  // polygon - 珊瑚橘點綴色
  ctx.beginPath();
  vals.forEach((v, i) => {
    const ratio = Math.max(0, Math.min(1, v / 100));
    const ang = (Math.PI * 2 * i) / keys.length - Math.PI / 2;
    const x = cx + Math.cos(ang) * (r * ratio);
    const y = cy + Math.sin(ang) * (r * ratio);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(255, 155, 130, .18)"; // 珊瑚橘填充
  ctx.strokeStyle = "rgba(255, 155, 130, .9)"; // 珊瑚橘線條
  ctx.lineWidth = 3;
  ctx.fill();
  ctx.stroke();

  ctx.setTransform(1, 0, 0, 1, 0, 0);
}


export function renderMetricBars(container, metrics, config = {}) {
  const items = config.items || Object.keys(metrics);
  const labels = config.labels || {}; // 可把 glow -> 光澤 等等映射
  const max = config.max ?? 100;

  container.innerHTML = "";

  items.forEach((key) => {
    const value = Number(metrics[key] ?? 0);
    const label = labels[key] ?? key;

    const row = document.createElement("div");
    row.style.display = "grid";
    row.style.gridTemplateColumns = "140px 1fr 56px";
    row.style.alignItems = "center";
    row.style.gap = "10px";

    const name = document.createElement("div");
    name.textContent = label;
    name.style.fontSize = "13px";
    name.style.color = "rgba(22,22,26,.78)";
    name.style.fontWeight = "700";

    const track = document.createElement("div");
    track.style.height = "14px";
    track.style.borderRadius = "999px";
    track.style.background = "rgba(0,0,0,.08)";
    track.style.overflow = "hidden";
    track.style.border = "1px solid rgba(0,0,0,.06)";

    const fill = document.createElement("div");
    fill.style.height = "100%";
    fill.style.width = `${Math.max(0, Math.min(100, (value / max) * 100))}%`;
    fill.style.borderRadius = "999px";
    fill.style.background = "linear-gradient(90deg, rgba(255,157,184,.95), rgba(242,216,140,.92))";

    track.appendChild(fill);

    const score = document.createElement("div");
    score.textContent = isFinite(value) ? String(Math.round(value)) : "--";
    score.style.textAlign = "right";
    score.style.fontWeight = "900";
    score.style.color = "rgba(22,22,26,.86)";

    row.appendChild(name);
    row.appendChild(track);
    row.appendChild(score);

    container.appendChild(row);
  });
}

// ========================================
// n8n API 整合函數
// ========================================

/**
 * Base64 轉 Blob
 * @param {string} base64 - Base64 字串
 * @returns {Blob} Blob 物件
 */
export function base64ToBlob(base64) {
  try {
    const parts = base64.split(',');
    const contentType = parts[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
    const raw = atob(parts[1]);
    const rawLength = raw.length;
    const uInt8Array = new Uint8Array(rawLength);

    for (let i = 0; i < rawLength; i++) {
      uInt8Array[i] = raw.charCodeAt(i);
    }

    return new Blob([uInt8Array], { type: contentType });
  } catch (error) {
    console.error('Base64 轉 Blob 失敗:', error);
    return null;
  }
}

/**
 * 提交分析到 n8n
 * @param {Object} options - 提交選項
 * @param {string} options.photoBase64 - 照片 Base64
 * @param {Object} options.answers - 問卷答案
 * @param {string} options.lineUserId - LINE User ID
 * @returns {Promise<Object>} 回傳 { success, session_id, message }
 */
export async function submitAnalysis({ photoBase64, answers, lineUserId }) {
  // 動態 import API 設定
  const { API_CONFIG, getAnalyzeUrl } = await import('./api-config.js');

  // 開發模式
  if (API_CONFIG.DEV_MODE) {
    console.log('📝 開發模式: 模擬提交分析');
    await new Promise(r => setTimeout(r, 1000)); // 模擬延遲
    const mockSessionId = 'dev_' + Date.now();
    localStorage.setItem('session_id', mockSessionId);
    return { success: true, session_id: mockSessionId, message: '開發模式' };
  }

  // 正式模式
  const analyzeUrl = getAnalyzeUrl();
  if (!analyzeUrl) {
    return { success: false, message: 'API URL 未設定' };
  }

  try {
    // 準備 FormData
    const formData = new FormData();

    // 加入照片
    if (photoBase64) {
      const blob = base64ToBlob(photoBase64);
      if (blob) {
        formData.append('photo', blob, 'user_photo.jpg');
      }
    }

    // 加入 LINE User ID
    formData.append('line_user_id', lineUserId || 'unknown');

    // 加入問卷答案 (JSON string)
    formData.append('answers', JSON.stringify(answers || {}));

    // 發送請求
    const response = await fetch(analyzeUrl, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (result.success && result.session_id) {
      localStorage.setItem('session_id', result.session_id);
      return result;
    }

    return { success: false, message: result.message || '提交失敗' };

  } catch (error) {
    console.error('提交分析失敗:', error);
    return { success: false, message: error.message || '網路錯誤' };
  }
}

/**
 * 取得分析結果
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} 分析結果
 */
export async function getAnalysisResult(sessionId) {
  const { API_CONFIG, getResultUrl } = await import('./api-config.js');

  // 開發模式: 使用 mock 資料
  if (API_CONFIG.DEV_MODE) {
    console.log('📝 開發模式: 使用 mock 資料');
    const response = await fetch('./api/mock_result.json');
    const data = await response.json();
    return { status: 'completed', ...data };
  }

  // 正式模式
  const resultUrl = getResultUrl(sessionId);

  try {
    const response = await fetch(resultUrl);
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('取得結果失敗:', error);
    return { status: 'failed', message: error.message };
  }
}

/**
 * 輪詢分析結果
 * @param {Object} options - 輪詢選項
 * @param {string} options.sessionId - Session ID
 * @param {Function} options.onProgress - 進度回調
 * @param {Function} options.onComplete - 完成回調
 * @param {Function} options.onError - 錯誤回調
 * @param {number} options.timeout - 超時時間 (毫秒)
 * @param {number} options.interval - 輪詢間隔 (毫秒)
 */
export function pollAnalysisResult({
  sessionId,
  onProgress,
  onComplete,
  onError,
  timeout = 30000,
  interval = 2000
}) {
  let elapsed = 0;

  const poll = async () => {
    try {
      const result = await getAnalysisResult(sessionId);

      if (result.status === 'completed') {
        onComplete?.(result);
        return;
      }

      if (result.status === 'failed') {
        onError?.(result.message || '分析失敗');
        return;
      }

      // 繼續輪詢
      elapsed += interval;

      if (elapsed >= timeout) {
        onError?.('分析超時,請稍後再試');
        return;
      }

      onProgress?.({ elapsed, timeout, status: result.status || 'processing' });
      setTimeout(poll, interval);

    } catch (error) {
      onError?.(error.message || '網路錯誤');
    }
  };

  // 開始輪詢
  poll();
}

/**
 * 取得 LINE User ID
 * @returns {string|null} LINE User ID
 */
export function getLineUserId() {
  // 先嘗試從 LIFF 取得
  if (typeof liff !== 'undefined' && liff.isLoggedIn && liff.isLoggedIn()) {
    try {
      const context = liff.getContext();
      return context?.userId || null;
    } catch (e) {
      console.warn('無法取得 LIFF context:', e);
    }
  }

  // 從 localStorage 取得 (如果之前有儲存)
  return localStorage.getItem('line_user_id') || null;
}
