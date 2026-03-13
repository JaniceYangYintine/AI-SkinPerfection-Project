/**
 * 相機模組
 * 處理相機開啟、臉部偵測、亮度偵測、拍照功能
 */

import { CONFIG, ERROR_MESSAGES, TIPS } from '../config.js';

// 模組狀態
let videoStream = null;
let videoElement = null;
let canvasElement = null;
let faceMesh = null;
let isDetecting = false;
let detectionInterval = null;

// 臉部偵測狀態
let faceState = {
    isAligned: false,
    isBrightEnough: false,
    tip: ''
};

// 回調函數
let onStateChange = null;

/**
 * 初始化相機模組
 * @param {Object} elements - DOM 元素
 * @param {HTMLVideoElement} elements.video - Video 元素
 * @param {HTMLCanvasElement} elements.canvas - Canvas 元素（用於截圖）
 * @param {HTMLCanvasElement} elements.overlay - Overlay Canvas（用於繪製框線）
 * @param {Function} stateCallback - 狀態變化回調
 */
export async function initCamera(elements, stateCallback) {
    videoElement = elements.video;
    canvasElement = elements.canvas;
    onStateChange = stateCallback;

    // 檢查瀏覽器支援
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error(ERROR_MESSAGES.CAMERA_NOT_SUPPORTED);
    }

    // 載入 MediaPipe Face Mesh
    await loadFaceMesh();
}

/**
 * 載入 MediaPipe Face Mesh
 */
async function loadFaceMesh() {
    // 檢查 MediaPipe 是否已載入
    if (typeof FaceMesh === 'undefined') {
        console.warn('[相機] MediaPipe FaceMesh 未載入，將使用簡化版臉部偵測');
        return;
    }

    try {
        console.log('[相機] 開始載入 MediaPipe Face Mesh...');

        faceMesh = new FaceMesh({
            locateFile: (file) => {
                // 正確的 CDN 路徑格式
                return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4/${file}`;
            }
        });

        faceMesh.setOptions({
            maxNumFaces: 1,
            refineLandmarks: false,  // 關閉精細偵測,提升速度
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        faceMesh.onResults(onFaceResults);

        console.log('[相機] ✅ MediaPipe Face Mesh 初始化成功');
    } catch (error) {
        console.error('[相機] ❌ MediaPipe Face Mesh 載入失敗:', error);
        faceMesh = null;  // 確保降級到簡化模式
    }
}

/**
 * 開啟相機
 */
export async function startCamera() {
    try {
        const constraints = {
            video: {
                facingMode: CONFIG.CAMERA.FACING_MODE,
                width: { ideal: CONFIG.CAMERA.WIDTH },
                height: { ideal: CONFIG.CAMERA.HEIGHT }
            },
            audio: false
        };

        videoStream = await navigator.mediaDevices.getUserMedia(constraints);
        videoElement.srcObject = videoStream;

        await new Promise((resolve) => {
            videoElement.onloadedmetadata = () => {
                videoElement.play();
                resolve();
            };
        });

        // 開始臉部偵測
        startDetection();

        return { success: true };

    } catch (error) {
        console.error('startCamera error:', error);

        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            throw new Error(ERROR_MESSAGES.CAMERA_PERMISSION_DENIED);
        }

        throw new Error(ERROR_MESSAGES.CAMERA_NOT_SUPPORTED);
    }
}

/**
 * 停止相機
 */
export function stopCamera() {
    stopDetection();
    if (faceMesh) {
        faceMesh.close(); // 釋放 MediaPipe 資源
        faceMesh = null;
    }
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }

    if (videoElement) {
        videoElement.srcObject = null;
    }
}

/**
 * 開始臉部偵測
 */
function startDetection() {
    if (isDetecting) return;
    isDetecting = true;

    detectionInterval = setInterval(() => {
        detectFace();
    }, CONFIG.CAMERA.FACE_DETECTION_INTERVAL);
}

/**
 * 停止臉部偵測
 */
function stopDetection() {
    isDetecting = false;
    if (detectionInterval) {
        clearInterval(detectionInterval);
        detectionInterval = null;
    }
}

/**
 * 偵測臉部
 */
async function detectFace() {
    if (!videoElement || videoElement.readyState !== 4) return;

    // 偵測亮度
    const brightness = detectBrightness();
    const isBrightEnough = brightness >= CONFIG.CAMERA.MIN_BRIGHTNESS;

    if (faceMesh) {
        // 使用 MediaPipe 偵測
        await faceMesh.send({ image: videoElement });
    } else {
        // 簡化版偵測（只檢查亮度）
        updateState({
            isAligned: true, // 沒有 MediaPipe 時，假設對齊
            isBrightEnough,
            tip: isBrightEnough ? TIPS.READY : ERROR_MESSAGES.BRIGHTNESS_LOW
        });
    }
}

/**
 * MediaPipe 臉部偵測結果回調
 */
function onFaceResults(results) {
    const brightness = detectBrightness();
    const isBrightEnough = brightness >= CONFIG.CAMERA.MIN_BRIGHTNESS;

    if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
        updateState({
            isAligned: false,
            isBrightEnough,
            tip: ERROR_MESSAGES.FACE_NOT_DETECTED
        });
        return;
    }

    const landmarks = results.multiFaceLandmarks[0];
    const alignmentResult = checkFaceAlignment(landmarks);

    updateState({
        isAligned: alignmentResult.isAligned,
        isBrightEnough,
        tip: !isBrightEnough ? ERROR_MESSAGES.BRIGHTNESS_LOW : alignmentResult.tip
    });
}

/**
 * 檢查臉部對齊
 * @param {Array} landmarks - 臉部特徵點
 * @returns {{isAligned: boolean, tip: string}}
 */
function checkFaceAlignment(landmarks) {
    // 取得關鍵點
    const nose = landmarks[1];       // 鼻尖
    const leftEye = landmarks[33];   // 左眼
    const rightEye = landmarks[263]; // 右眼
    const chin = landmarks[152];     // 下巴

    // 計算臉部中心
    const centerX = nose.x;
    const centerY = (nose.y + chin.y) / 2;

    // 計算臉部大小（眼距）
    const eyeDistance = Math.abs(rightEye.x - leftEye.x);

    // 從 config 取得設定值
    const { FACE_DETECTION } = CONFIG.CAMERA;
    const idealCenterX = FACE_DETECTION.IDEAL_X;
    const idealCenterY = FACE_DETECTION.IDEAL_Y;
    const idealSize = FACE_DETECTION.IDEAL_SIZE;
    const tolerancePosition = FACE_DETECTION.TOLERANCE_POSITION;
    const toleranceSize = FACE_DETECTION.TOLERANCE_SIZE;

    // 檢查位置
    const isXAligned = Math.abs(centerX - idealCenterX) < tolerancePosition;
    const isYAligned = Math.abs(centerY - idealCenterY) < tolerancePosition;
    const isSizeOk = Math.abs(eyeDistance - idealSize) < toleranceSize;

    // 決定提示
    let tip = TIPS.PERFECT;
    let isAligned = true;

    if (!isSizeOk) {
        isAligned = false;
        tip = eyeDistance < idealSize ? TIPS.FACE_TOO_FAR : TIPS.FACE_TOO_CLOSE;
    } else if (!isXAligned) {
        isAligned = false;
        tip = centerX < idealCenterX ? TIPS.FACE_RIGHT : TIPS.FACE_LEFT;
    } else if (!isYAligned) {
        isAligned = false;
        tip = centerY < idealCenterY ? TIPS.FACE_DOWN : TIPS.FACE_UP;
    }

    return { isAligned, tip };
}

/**
 * 偵測畫面亮度
 * @returns {number} 平均亮度值 (0-255)
 */
function detectBrightness() {
    if (!videoElement || !canvasElement) return 255;

    const ctx = canvasElement.getContext('2d');
    const { BRIGHTNESS } = CONFIG.CAMERA;
    const sampleSize = BRIGHTNESS.SAMPLE_SIZE;

    canvasElement.width = sampleSize;
    canvasElement.height = sampleSize;

    ctx.drawImage(videoElement, 0, 0, sampleSize, sampleSize);

    try {
        const imageData = ctx.getImageData(0, 0, sampleSize, sampleSize);
        const data = imageData.data;
        const { R, G, B } = BRIGHTNESS.COEFFICIENTS;
        let sum = 0;

        for (let i = 0; i < data.length; i += 4) {
            // 計算灰階亮度 (ITU-R BT.601 標準)
            sum += (data[i] * R + data[i + 1] * G + data[i + 2] * B);
        }

        return sum / (sampleSize * sampleSize);
    } catch (e) {
        return 255; // 出錯時預設亮度足夠
    }
}

/**
 * 更新狀態並通知
 */
function updateState(newState) {
    const hasChanged =
        faceState.isAligned !== newState.isAligned ||
        faceState.isBrightEnough !== newState.isBrightEnough ||
        faceState.tip !== newState.tip;

    faceState = { ...newState };

    if (hasChanged && onStateChange) {
        onStateChange({
            ...faceState,
            canCapture: faceState.isAligned && faceState.isBrightEnough
        });
    }
}

/**
 * 拍照
 * @returns {Promise<{success: boolean, blob?: Blob, previewUrl?: string, error?: string}>}
 */
export async function capturePhoto() {
    if (!videoElement || !canvasElement) {
        return { success: false, error: '相機未初始化' };
    }

    try {
        const ctx = canvasElement.getContext('2d');

        // 固定輸出尺寸（4:3），使用中心裁切保持比例
        const outputWidth = CONFIG.CAMERA.OUTPUT_WIDTH;
        const outputHeight = CONFIG.CAMERA.OUTPUT_HEIGHT;

        const sourceWidth = videoElement.videoWidth;
        const sourceHeight = videoElement.videoHeight;

        const outputRatio = outputWidth / outputHeight;
        const sourceRatio = sourceWidth / sourceHeight;

        let sx = 0;
        let sy = 0;
        let sWidth = sourceWidth;
        let sHeight = sourceHeight;

        if (sourceRatio > outputRatio) {
            sWidth = Math.round(sourceHeight * outputRatio);
            sx = Math.round((sourceWidth - sWidth) / 2);
        } else if (sourceRatio < outputRatio) {
            sHeight = Math.round(sourceWidth / outputRatio);
            sy = Math.round((sourceHeight - sHeight) / 2);
        }

        canvasElement.width = outputWidth;
        canvasElement.height = outputHeight;

        // 水平翻轉（前鏡頭鏡像）
        ctx.translate(outputWidth, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(videoElement, sx, sy, sWidth, sHeight, 0, 0, outputWidth, outputHeight);

        // 轉為 JPEG Blob
        const blob = await new Promise((resolve) => {
            canvasElement.toBlob((b) => resolve(b), 'image/jpeg', CONFIG.CAMERA.IMAGE_QUALITY);
        });

        if (!blob) {
            return { success: false, error: '拍照失敗，請重試' };
        }

        const previewUrl = URL.createObjectURL(blob);
        return { success: true, blob, previewUrl };

    } catch (error) {
        console.error('capturePhoto error:', error);
        return { success: false, error: '拍照失敗，請重試' };
    }
}

/**
 * 取得目前臉部狀態
 */
export function getFaceState() {
    return {
        ...faceState,
        canCapture: faceState.isAligned && faceState.isBrightEnough
    };
}

/**
 * 取得儲存的照片
 */
export function getSavedPhoto() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.PHOTO);
}

/**
 * 清除儲存的照片
 */
export function clearSavedPhoto() {
    localStorage.removeItem(CONFIG.STORAGE_KEYS.PHOTO);
}
