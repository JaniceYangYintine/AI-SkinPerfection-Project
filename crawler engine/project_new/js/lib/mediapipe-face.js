// assets/mediapipe-face.js
import vision from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";
import { saveResult, toast, safeJsonFetch } from "./app.js";

const { FaceLandmarker, FilesetResolver, DrawingUtils } = vision;

// import {
//   FaceLandmarker,
//   FilesetResolver,
//   DrawingUtils
// } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";

let faceLandmarker, drawingUtils;
let running = false;

let lastSentAt = 0;
let lastPhotoAt = 0;
const SEND_INTERVAL_MS = 350;    // 數值送後端頻率
const PHOTO_INTERVAL_MS = 5000;  // 照片送後端頻率（避免爆）

function captureJpegDataUrl(video, maxWidth = 640, quality = 0.72) {
  const scale = Math.min(1, maxWidth / video.videoWidth);
  const w = Math.round(video.videoWidth * scale);
  const h = Math.round(video.videoHeight * scale);

  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const cctx = c.getContext("2d");
  cctx.drawImage(video, 0, 0, w, h);
  return c.toDataURL("image/jpeg", quality);
}

async function initModel() {
  const fileset = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
  );

  faceLandmarker = await FaceLandmarker.createFromOptions(fileset, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
      delegate: "GPU",
    },
    runningMode: "VIDEO",
    numFaces: 1,
    outputFaceBlendshapes: true,
    outputFacialTransformationMatrixes: false,
  });
}

async function startCamera(video) {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user" },
    audio: false,
  });
  video.srcObject = stream;

  await new Promise((res) => (video.onloadedmetadata = res));
  await video.play();

  return stream;
}

// 後端 API：你現在是 PHP，所以走 ./api/analyze.php
// 這裡用 JSON 送（含數值 + 偶爾一張照片）
// 你後端要能吃 JSON；如果你現在 analyze.php 只吃 FormData，跟我說我再改成 FormData 版本
async function sendToBackend(payload) {
  const r = await safeJsonFetch("./api/analyze.php", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }, null);

  if (!r.ok) throw new Error(r.data?.message || "後端回傳失敗");
  return r.data;
}

function loop(video, canvas, ctx) {
  if (!running) return;

  const now = performance.now();
  const result = faceLandmarker.detectForVideo(video, now);

  // --- 畫網格 ---
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (result.faceLandmarks?.length) {
    for (const landmarks of result.faceLandmarks) {
      drawingUtils.drawConnectors(
        landmarks,
        FaceLandmarker.FACE_LANDMARKS_TESSELATION,
        { lineWidth: 1 }
      );
    }
  }

  // --- 送後端（數值 + 偶爾照片）---
  if (result.faceBlendshapes?.[0] && (now - lastSentAt) > SEND_INTERVAL_MS) {
    lastSentAt = now;

    const blend = result.faceBlendshapes[0].categories ?? [];
    const payload = {
      ts: Date.now(),
      blendshapes: blend.map(c => ({ name: c.categoryName, score: c.score })),
    };

    const shouldAttachPhoto = (now - lastPhotoAt) > PHOTO_INTERVAL_MS;
    if (shouldAttachPhoto) {
      lastPhotoAt = now;
      payload.image = {
        mime: "image/jpeg",
        dataUrl: captureJpegDataUrl(video, 640, 0.72),
      };
    }

    sendToBackend(payload)
      .then((data) => {
        // 把後端回傳存起來，result.html 會讀 RESULT_KEY 顯示
        saveResult(data);
      })
      .catch((e) => {
        // 不要一直噴 toast，避免每幀刷屏
        console.warn(e);
      });
  }

  requestAnimationFrame(() => loop(video, canvas, ctx));
}

export async function startFaceMesh() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("meshCanvas");

  if (!video || !canvas) {
    toast("找不到 #cameraVideo 或 #meshCanvas，請確認 analyze.html 有放 video/canvas");
    return;
  }

  const ctx = canvas.getContext("2d");

  if (!faceLandmarker) await initModel();
  drawingUtils = new DrawingUtils(ctx);

  const stream = await startCamera(video);

  // 同步 canvas 尺寸到 video
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  running = true;
  loop(video, canvas, ctx);

  toast("網格偵測啟動 ✅");

  // 回傳停止函式（可選）
  return () => {
    running = false;
    stream.getTracks().forEach(t => t.stop());
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    toast("已停止");
  };
}
