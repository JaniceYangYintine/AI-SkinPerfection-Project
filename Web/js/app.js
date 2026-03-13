/**
 * 主程式入口
 * 管理應用程式狀態、頁面切換、整合各模組
 */

import { CONFIG, ERROR_MESSAGES } from './config.js';
import { initCamera, startCamera, stopCamera, capturePhoto } from './modules/camera.js';
import { initSurvey, renderSurvey, getAllAnswers, resetSurvey, isComplete as isSurveyComplete } from './modules/survey.js';
import { initResult, setResultData } from './modules/result.js';
import { submitAnalysis, pollResult } from './utils/api.js';
import { initLiff } from './utils/liff.js';

// ==================== 應用程式狀態 ====================

const AppState = {
    currentSection: 'camera',  // camera | survey | loading | result
    photoBlob: null,
    photoUrl: null,
    answers: {},
    sessionId: null,
    resultData: null,
    isLoading: false
};

// ==================== DOM 元素 ====================

const elements = {
    app: null,
    sections: {
        camera: null,
        survey: null,
        loading: null,
        result: null
    },
    camera: {
        video: null,
        canvas: null,
        overlay: null,
        captureBtn: null,
        tip: null
    },
    survey: {
        container: null
    },
    loading: {
        text: null,
        progress: null
    },
    result: {
        container: null
    }
};

// ==================== 初始化 ====================

/**
 * 應用程式初始化
 */
export async function initApp() {
    console.log('🚀 Skincare App 初始化中...');

    // 取得 DOM 元素
    cacheElements();

    // 初始化 LIFF（不阻斷流程）
    await initLiff();

    // 初始化問卷模組
    initSurvey({
        onProgressChange: handleSurveyProgress,
        onComplete: handleSurveyComplete
    });

    // 顯示相機區塊
    await goToSection('camera');

    console.log('✅ Skincare App 初始化完成');
}

/**
 * 快取 DOM 元素
 */
function cacheElements() {
    elements.app = document.getElementById('app');

    // 區塊
    elements.sections.camera = document.getElementById('section-camera');
    elements.sections.survey = document.getElementById('section-survey');
    elements.sections.loading = document.getElementById('section-loading');
    elements.sections.result = document.getElementById('section-result');

    // 相機元素
    elements.camera.video = document.getElementById('cameraVideo');
    elements.camera.canvas = document.getElementById('cameraCanvas');
    elements.camera.overlay = document.getElementById('cameraOverlay');
    elements.camera.captureBtn = document.getElementById('captureBtn');
    elements.camera.tip = document.getElementById('cameraTip');

    // 問卷元素
    elements.survey.container = document.getElementById('surveyContainer');

    // Loading 元素
    elements.loading.text = document.getElementById('loadingText');
    elements.loading.progress = document.getElementById('loadingProgress');

    // 結果元素
    elements.result.container = document.getElementById('resultContainer');
}

// ==================== 頁面切換 ====================

/**
 * 切換到指定區塊
 */
async function goToSection(sectionName) {
    // 隱藏所有區塊
    Object.values(elements.sections).forEach(section => {
        if (section) {
            section.classList.remove('active');
        }
    });

    // 離開當前區塊的清理
    if (AppState.currentSection === 'camera' && sectionName !== 'camera') {
        stopCamera();
    }

    // 顯示目標區塊
    const targetSection = elements.sections[sectionName];
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // 進入新區塊的初始化
    switch (sectionName) {
        case 'camera':
            await initCameraSection();
            break;
        case 'survey':
            initSurveySection();
            break;
        case 'loading':
            // Loading 不需要特別初始化
            break;
        case 'result':
            initResultSection();
            break;
    }

    AppState.currentSection = sectionName;
    console.log(`📍 切換到: ${sectionName}`);
}

// ==================== 相機區塊 ====================

/**
 * 初始化相機區塊
 */
async function initCameraSection() {
    try {
        // 初始化相機模組
        await initCamera({
            video: elements.camera.video,
            canvas: elements.camera.canvas,
            overlay: elements.camera.overlay
        }, handleCameraStateChange);

        // 開啟相機
        await startCamera();

        // 綁定拍照按鈕
        if (elements.camera.captureBtn) {
            elements.camera.captureBtn.onclick = handleCapture;
        }

    } catch (error) {
        console.error('相機初始化失敗:', error);
        showCameraTip(error.message, 'error');
    }
}

/**
 * 處理相機狀態變化
 */
function handleCameraStateChange(state) {
    // 更新提示文字
    showCameraTip(state.tip, state.canCapture ? 'success' : 'warning');

    // 更新拍照按鈕狀態
    if (elements.camera.captureBtn) {
        elements.camera.captureBtn.disabled = !state.canCapture;
        elements.camera.captureBtn.classList.toggle('ready', state.canCapture);
    }
}

/**
 * 顯示相機提示
 */
function showCameraTip(message, type = 'info') {
    if (elements.camera.tip) {
        elements.camera.tip.textContent = message;
        elements.camera.tip.className = `camera-tip ${type}`;
    }
}

/**
 * 處理拍照
 */
async function handleCapture() {
    const result = await capturePhoto();

    if (result.success) {
        if (AppState.photoUrl) {
            URL.revokeObjectURL(AppState.photoUrl);
        }
        AppState.photoBlob = result.blob;
        AppState.photoUrl = result.previewUrl;
        console.log('📸 拍照成功');

        // 顯示預覽
        showPhotoPreview(result.previewUrl);

    } else {
        alert(result.error || '拍照失敗，請重試');
    }
}

/**
 * 顯示照片預覽
 */
function showPhotoPreview(photoData) {
    // 建立預覽 Modal
    const modal = document.createElement('div');
    modal.className = 'photo-preview-modal';
    modal.innerHTML = `
        <div class="preview-content">
            <img src="${photoData}" alt="預覽照片" class="preview-image">
            <div class="preview-actions">
                <button class="btn btn-secondary" id="retakeBtn">重新拍照</button>
                <button class="btn btn-primary" id="usePhotoBtn">使用照片</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // 綁定事件
    modal.querySelector('#retakeBtn').onclick = () => {
        modal.remove();
        // 繼續使用相機
    };

    modal.querySelector('#usePhotoBtn').onclick = () => {
        modal.remove();
        goToSection('survey');
    };
}

// ==================== 問卷區塊 ====================

/**
 * 初始化問卷區塊
 */
function initSurveySection() {
    if (elements.survey.container) {
        renderSurvey(elements.survey.container);
    }

    // 顯示照片預覽
    if (AppState.photoUrl) {
        showPhotoThumbnail();
    }
}

/**
 * 顯示照片縮圖
 */
function showPhotoThumbnail() {
    const thumbnail = document.getElementById('photoThumbnail');
    if (thumbnail && AppState.photoUrl) {
        thumbnail.src = AppState.photoUrl;
        thumbnail.style.display = 'block';
    }
}

/**
 * 處理問卷進度變化
 */
function handleSurveyProgress(progress) {
    console.log(`📝 問卷進度: ${progress.current}/${progress.total}`);
}

/**
 * 處理問卷完成
 */
async function handleSurveyComplete(answers) {
    console.log('✅ 問卷完成', answers);
    AppState.answers = answers;

    // 送出分析
    await submitForAnalysis();
}

// ==================== Loading 區塊 ====================

/**
 * 送出分析請求
 */
async function submitForAnalysis() {
    goToSection('loading');
    updateLoadingStatus('正在上傳資料...', 10);

    try {
        // 送出分析請求
        const submitResult = await submitAnalysis(AppState.photoBlob, AppState.answers);

        if (!submitResult.success) {
            throw new Error(submitResult.error);
        }

        AppState.sessionId = submitResult.session_id;
        updateLoadingStatus('AI 分析中...', 30);

        // 輪詢取得結果
        const resultData = await pollResult(AppState.sessionId, (progress) => {
            updateLoadingStatus('AI 分析中...', 30 + progress * 0.6);
        });

        if (!resultData.success) {
            throw new Error(resultData.error);
        }

        AppState.resultData = resultData.data;
        updateLoadingStatus('分析完成！', 100);

        // 跳轉到結果頁
        setTimeout(() => {
            goToSection('result');
        }, 500);

    } catch (error) {
        console.error('分析失敗:', error);
        showLoadingError(error.message);
    }
}

/**
 * 更新 Loading 狀態
 */
function updateLoadingStatus(text, progress) {
    if (elements.loading.text) {
        elements.loading.text.textContent = text;
    }
    if (elements.loading.progress) {
        elements.loading.progress.style.width = `${progress}%`;
    }
}

/**
 * 顯示 Loading 錯誤
 */
function showLoadingError(message) {
    const loadingSection = elements.sections.loading;
    if (loadingSection) {
        loadingSection.innerHTML = `
            <div class="loading-error">
                <div class="error-icon">❌</div>
                <p class="error-message">${message}</p>
                <button class="btn btn-primary" id="retryBtn">重試</button>
                <button class="btn btn-secondary" id="backToSurveyBtn">返回問卷</button>
            </div>
        `;

        loadingSection.querySelector('#retryBtn').onclick = submitForAnalysis;
        loadingSection.querySelector('#backToSurveyBtn').onclick = () => goToSection('survey');
    }
}

// ==================== 結果區塊 ====================

/**
 * 初始化結果區塊
 */
function initResultSection() {
    if (elements.result.container && AppState.resultData) {
        initResult(elements.result.container, AppState.resultData);
    }
}

// ==================== 匯出全域 API ====================

// 讓其他模組可以存取
window.SkincareApp = {
    goToSection,
    getState: () => ({ ...AppState }),
    resetApp: () => {
        resetSurvey();
        if (AppState.photoUrl) {
            URL.revokeObjectURL(AppState.photoUrl);
        }
        AppState.photoBlob = null;
        AppState.photoUrl = null;
        AppState.answers = {};
        AppState.sessionId = null;
        AppState.resultData = null;
        goToSection('camera');
    }
};

// ==================== 啟動應用程式 ====================

// DOM 載入完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
