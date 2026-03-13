/**
 * 結果頁模組
 * ======================================================
 * 處理分析結果的顯示
 * - 總覽頁：四大區塊摘要卡片
 * - 詳細頁：單頁垂直滾動，顯示全部 A/B/C/D 區
 * - Sticky 導航：固定在頂部，點擊快速跳轉
 * - 滾動偵測：自動高亮當前區塊
 * 更新：2026-02-03
 */

import { CONFIG, ICON_PATHS } from '../config.js';
import { drawRadarChartWithValues, drawRadarChartAnimated } from './radar.js?v=1.1';
import { buildAnalysisFlexMessage } from '../utils/flexMessage.js';
import { initCarousel, get, isLiffLoggedIn, showToast } from '../utils/helpers.js';
import { extractSummary, renderSummary, bindSummaryEvents } from './summary.js';

// ==================== 模組狀態 ====================
let resultData = null;
let currentView = CONFIG.RESULT.DEFAULT_VIEW; // 'summary' | 'detail'
let currentTab = CONFIG.RESULT.DEFAULT_TAB;
let containerElement = null;
let scrollObserver = null; // IntersectionObserver 實例

// 輪播實例（用於清理）
let carouselInstances = [];

/**
 * 初始化結果頁模組
 * @param {HTMLElement} container - 容器元素
 * @param {Object} data - 後端回傳的結果資料
 */
export function initResult(container, data) {
    containerElement = container;
    resultData = data;
    currentView = CONFIG.RESULT.DEFAULT_VIEW;
    currentTab = CONFIG.RESULT.DEFAULT_TAB;

    render();
}

/**
 * 主渲染函式：根據 currentView 決定顯示總覽或詳情
 */
function render() {
    if (!containerElement || !resultData) return;

    // 清理舊的 Observer
    if (scrollObserver) {
        scrollObserver.disconnect();
        scrollObserver = null;
    }

    if (currentView === 'summary') {
        renderSummaryView();
    } else {
        renderDetailView();
    }
}

/**
 * 渲染總覽頁面
 */
function renderSummaryView() {
    // 清理舊的輪播實例
    carouselInstances.forEach(instance => instance?.destroy?.());
    carouselInstances = [];

    // 提取摘要資料
    const summaryData = extractSummary(resultData);

    containerElement.innerHTML = `
        <div class="result-wrapper organic-bg">
            ${renderSummary(summaryData)}

            <!-- 儲存報告按鈕 -->
            <div class="result-actions">
                <button class="btn btn-primary btn-save-report" id="saveReportBtn" aria-label="儲存報告並分享到 LINE">
                    至選單領取你的專屬報告
                </button>
            </div>
        </div>
    `;

    // 綁定總覽頁事件
    bindSummaryEvents(containerElement, handleViewDetail);

    // 綁定儲存按鈕事件
    const saveBtn = containerElement.querySelector('#saveReportBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', handleSaveReport);
    }
}

/**
 * 處理「查看詳情」點擊
 * @param {string} tab - 目標 Tab (A/B/C/D)
 */
function handleViewDetail(tab) {
    currentView = 'detail';
    currentTab = tab;
    render();

    // 渲染完成後，滾動到指定區塊
    // 使用 requestAnimationFrame 確保 DOM 已更新
    requestAnimationFrame(() => {
        // 再等待一幀確保佈局計算完成
        requestAnimationFrame(() => {
            scrollToSection(tab);
        });
    });
}

/**
 * 渲染詳情頁面（單頁垂直滾動，顯示全部 A/B/C/D）
 */
function renderDetailView() {
    if (!containerElement || !resultData) return;

    // 清理舊的輪播實例
    carouselInstances.forEach(instance => instance?.destroy?.());
    carouselInstances = [];

    containerElement.innerHTML = `
        <div class="result-wrapper detail-view organic-bg">
            <!-- 固定頂部區域：返回 + ABCD 同一排 -->
            <div class="detail-header">
                <nav class="header-nav" role="navigation" aria-label="結果頁導航">
                    <!-- 返回總覽按鈕 -->
                    <button class="btn-back-summary" id="backToSummaryBtn" aria-label="返回總覽">
                        <span class="back-arrow">←</span>
                    </button>

                    <!-- Tab 導航 -->
                    <div class="tab-nav sticky-nav" role="tablist" aria-label="分析結果分類">
                        ${CONFIG.RESULT.TABS.map(tab => `
                            <button
                                class="tab-btn ${tab === currentTab ? 'active' : ''}"
                                data-tab="${tab}"
                                role="tab"
                                aria-selected="${tab === currentTab}"
                            >
                                ${tab}
                            </button>
                        `).join('')}
                    </div>
                </nav>
            </div>

            <!-- 滾動內容區（軟吸附） -->
            <div class="detail-content">
                <!-- A 區：活力氣色指南 -->
                <section id="section-A" class="detail-section" data-section="A">
                    <div class="section-card">
                        <div class="section-card-header">
                            <span class="section-badge">A</span>
                            <h2 class="section-card-title">活力氣色指南</h2>
                        </div>
                        <div class="section-card-body">
                            ${renderSectionA()}
                        </div>
                    </div>
                </section>

                <!-- B 區：智能膚況解析 -->
                <section id="section-B" class="detail-section" data-section="B">
                    <div class="section-card">
                        <div class="section-card-header">
                            <span class="section-badge">B</span>
                            <h2 class="section-card-title">智能膚況解析</h2>
                        </div>
                        <div class="section-card-body">
                            ${renderSectionB()}
                        </div>
                    </div>
                </section>

                <!-- C 區：由內而外養膚 -->
                <section id="section-C" class="detail-section" data-section="C">
                    <div class="section-card">
                        <div class="section-card-header">
                            <span class="section-badge">C</span>
                            <h2 class="section-card-title">由內而外養膚</h2>
                        </div>
                        <div class="section-card-body">
                            ${renderSectionC()}
                        </div>
                    </div>
                </section>

                <!-- D 區：智慧配方 -->
                <section id="section-D" class="detail-section" data-section="D">
                    <div class="section-card">
                        <div class="section-card-header">
                            <span class="section-badge">D</span>
                            <h2 class="section-card-title">智慧配方</h2>
                        </div>
                        <div class="section-card-body">
                            ${renderSectionD()}
                        </div>
                    </div>
                </section>
            </div>

            <!-- 儲存報告按鈕 -->
            <div class="result-actions">
                <button class="btn btn-primary btn-save-report" id="saveReportBtn" aria-label="儲存報告並分享到 LINE">
                    至選單領取你的專屬報告
                </button>
            </div>

            <!-- 返回頂部按鈕 -->
            <button class="back-to-top" id="backToTop" aria-label="返回頂部">
                <span aria-hidden="true">↑</span>
            </button>
        </div>
        
        <!-- 圖片放大 Lightbox (移到外層，不受限於 D 區) -->
        <div class="image-lightbox" id="imageLightbox" aria-hidden="true">
            <button class="lightbox-close" aria-label="關閉">&times;</button>
            <div class="lightbox-content">
                <img src="" alt="" class="lightbox-image" id="lightboxImage">
            </div>
            <p class="lightbox-hint">快速點擊兩下放大 · 拖曳移動 · 點擊關閉</p>
        </div>
    `;

    // 綁定事件
    bindDetailEvents();

    // 初始化各區塊的元件
    initAllSections();

    // 初始化滾動偵測
    initScrollObserver();

    // 初始化返回頂部按鈕
    initBackToTop();
}

/**
 * 初始化所有區塊的元件（雷達圖、輪播等）
 */
function initAllSections() {
    // 繪製雷達圖（B 區）
    const radarCanvas = containerElement.querySelector('#radarChart');
    if (radarCanvas && resultData.sectionB?.scores) {
        // 使用 IntersectionObserver 延遲繪製，提升效能
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    drawRadarChartAnimated(radarCanvas, resultData.sectionB.scores);
                    observer.disconnect();
                }
            });
        }, { threshold: 0.1 });
        observer.observe(radarCanvas);
    }

    // 初始化按摩輪播（A 區）
    initMassageCarousel();

    // 初始化圓形進度環動畫（A 區）
    initCircularProgress();

    // 初始化產品輪播（D 區）
    initProductsCarousel();

    // 初始化圖片放大功能
    initImageLightbox();
}

/**
 * 初始化圖片放大 Lightbox（支援縮放與拖曳）
 */
function initImageLightbox() {
    const lightbox = containerElement.querySelector('#imageLightbox');
    const lightboxImage = containerElement.querySelector('#lightboxImage');
    const lightboxClose = containerElement.querySelector('.lightbox-close');
    const lightboxContent = containerElement.querySelector('.lightbox-content');
    const zoomableContainers = containerElement.querySelectorAll('[data-zoomable]');

    if (!lightbox || !lightboxImage || zoomableContainers.length === 0) return;

    // 縮放與拖曳狀態
    let scale = 1;
    let posX = 0;
    let posY = 0;
    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let lastPosX = 0;
    let lastPosY = 0;
    let initialDistance = 0;
    let initialScale = 1;

    const MIN_SCALE = 1;
    const MAX_SCALE = 4;

    // 開啟 lightbox
    function openLightbox(imgSrc, imgAlt) {
        lightboxImage.src = imgSrc;
        lightboxImage.alt = imgAlt || '';
        resetTransform();
        lightbox.classList.add('active');
        lightbox.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';

        // 禁用頁面的觸控縮放
        document.addEventListener('touchmove', preventZoom, { passive: false });
    }

    // 關閉 lightbox
    function closeLightbox() {
        lightbox.classList.remove('active');
        lightbox.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';

        // 恢復頁面的觸控縮放
        document.removeEventListener('touchmove', preventZoom);
    }

    // 防止頁面縮放的函數
    function preventZoom(e) {
        if (e.touches.length > 1) {
            e.preventDefault();
        }
    }

    // 重設變形
    function resetTransform() {
        scale = 1;
        posX = 0;
        posY = 0;
        updateTransform();
    }

    // 更新圖片變形（使用 RAF 優化性能）
    let rafId = null;
    function updateTransform() {
        if (rafId) {
            cancelAnimationFrame(rafId);
        }
        rafId = requestAnimationFrame(() => {
            lightboxImage.style.transform = `translate(${posX}px, ${posY}px) scale(${scale})`;
            rafId = null;
        });
    }

    // 限制拖曳範圍
    function clampPosition() {
        const rect = lightboxImage.getBoundingClientRect();
        const containerRect = lightboxContent.getBoundingClientRect();

        const maxX = Math.max(0, (rect.width - containerRect.width) / 2);
        const maxY = Math.max(0, (rect.height - containerRect.height) / 2);

        posX = Math.max(-maxX, Math.min(maxX, posX));
        posY = Math.max(-maxY, Math.min(maxY, posY));
    }

    // 計算兩指距離
    function getDistance(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    // 點擊可縮放圖片容器
    zoomableContainers.forEach(container => {
        const img = container.querySelector('img');
        if (img) {
            container.addEventListener('click', () => {
                openLightbox(img.src, img.alt);
            });
        }
    });

    // 關閉按鈕
    lightboxClose.addEventListener('click', closeLightbox);

    // 點擊背景關閉（只在未縮放時）
    lightboxContent.addEventListener('click', (e) => {
        if (e.target === lightboxContent && scale === 1) {
            closeLightbox();
        }
    });

    // ESC 關閉
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && lightbox.classList.contains('active')) {
            closeLightbox();
        }
    });

    // 滑鼠滾輪縮放
    lightboxContent.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.2 : 0.2;
        scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale + delta));
        if (scale === 1) {
            posX = 0;
            posY = 0;
        } else {
            clampPosition();
        }
        updateTransform();
    }, { passive: false });

    // 滑鼠拖曳
    lightboxImage.addEventListener('mousedown', (e) => {
        if (scale > 1) {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            lastPosX = posX;
            lastPosY = posY;
            lightboxImage.style.cursor = 'grabbing';
        }
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        posX = lastPosX + (e.clientX - startX);
        posY = lastPosY + (e.clientY - startY);
        clampPosition();
        updateTransform();
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        lightboxImage.style.cursor = scale > 1 ? 'grab' : 'zoom-out';
    });

    // 觸控：拖曳與雙指縮放
    lightboxContent.addEventListener('touchstart', (e) => {
        // 防止瀏覽器預設的縮放行為
        if (e.touches.length >= 2) {
            e.preventDefault();
        }

        if (e.touches.length === 1 && scale > 1) {
            isDragging = true;
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            lastPosX = posX;
            lastPosY = posY;
        } else if (e.touches.length === 2) {
            isDragging = false;
            initialDistance = getDistance(e.touches);
            initialScale = scale;
        }
    }, { passive: false });

    lightboxContent.addEventListener('touchmove', (e) => {
        if (e.touches.length === 1 && isDragging) {
            e.preventDefault();
            posX = lastPosX + (e.touches[0].clientX - startX);
            posY = lastPosY + (e.touches[0].clientY - startY);
            clampPosition();
            updateTransform();
        } else if (e.touches.length === 2) {
            e.preventDefault();
            const currentDistance = getDistance(e.touches);
            const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, initialScale * (currentDistance / initialDistance)));

            // 平滑過渡
            scale = newScale;

            if (scale === 1) {
                posX = 0;
                posY = 0;
            }
            updateTransform();
        }
    }, { passive: false });

    lightboxContent.addEventListener('touchend', (e) => {
        if (e.touches.length === 0) {
            isDragging = false;
        }
    }, { passive: true });

    // 雙擊縮放
    let lastTap = 0;
    lightboxContent.addEventListener('touchend', (e) => {
        const now = Date.now();
        if (now - lastTap < 300 && e.changedTouches.length === 1) {
            e.preventDefault();
            if (scale > 1) {
                resetTransform();
            } else {
                scale = 2.5;
                updateTransform();
            }
        }
        lastTap = now;
    }, { passive: false });
}

// 控制是否允許 Observer 更新 Tab（點擊跳轉時暫停）
let isScrollingByClick = false;
let scrollTimeout = null;

/**
 * 初始化滾動偵測（IntersectionObserver）
 * 1. 滾動時自動高亮當前區塊對應的 Tab
 * 2. 卡片進入畫面時播放進場動畫
 */
function initScrollObserver() {
    const sections = containerElement.querySelectorAll('.detail-section');
    const sectionCards = containerElement.querySelectorAll('.section-card');

    if (sections.length === 0) return;

    // Observer: Tab 高亮（只在非點擊滾動時才更新）
    scrollObserver = new IntersectionObserver((entries) => {
        // 如果是點擊觸發的滾動，不更新 Tab
        if (isScrollingByClick) return;

        // 找出目前可見比例最高的區塊
        let maxRatio = 0;
        let visibleSection = null;

        entries.forEach(entry => {
            if (entry.isIntersecting && entry.intersectionRatio > maxRatio) {
                maxRatio = entry.intersectionRatio;
                visibleSection = entry.target.dataset.section;
            }
        });

        if (visibleSection) {
            updateActiveTab(visibleSection);
        }
    }, {
        root: null,
        rootMargin: '-30% 0px -50% 0px',
        threshold: [0, 0.25, 0.5, 0.75, 1]
    });

    sections.forEach(section => {
        scrollObserver.observe(section);
    });

    // Observer 2: 卡片進場動畫
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                cardObserver.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        rootMargin: '0px 0px -10% 0px',
        threshold: 0.1
    });

    sectionCards.forEach(card => {
        cardObserver.observe(card);
    });
}

/**
 * 更新當前 active 的 Tab
 */
function updateActiveTab(sectionId) {
    if (!sectionId || sectionId === currentTab) return;

    const tabBtns = containerElement.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === sectionId) {
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
        } else {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
        }
    });
    currentTab = sectionId;
}

/**
 * 滾動到指定區塊
 */
function scrollToSection(sectionId) {
    const section = containerElement.querySelector(`#section-${sectionId}`);
    if (!section) {
        console.warn(`Section #section-${sectionId} not found`);
        return;
    }

    // 標記：正在進行點擊觸發的滾動，暫停 Observer 更新
    isScrollingByClick = true;

    // 清除之前的 timeout
    if (scrollTimeout) {
        clearTimeout(scrollTimeout);
    }

    // 先立即更新 Tab 狀態
    updateActiveTab(sectionId);

    // 執行滾動
    section.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });

    // 滾動完成後恢復 Observer（預估 600ms 完成滾動）
    scrollTimeout = setTimeout(() => {
        isScrollingByClick = false;
    }, 600);
}

/**
 * 綁定詳細頁事件
 */
function bindDetailEvents() {
    // 返回總覽按鈕
    const backBtn = containerElement.querySelector('#backToSummaryBtn');
    if (backBtn) {
        backBtn.addEventListener('click', handleBackToSummary);
    }

    // Tab 點擊（快速跳轉）
    const tabBtns = containerElement.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tab = e.currentTarget.dataset.tab;
            if (tab) {
                scrollToSection(tab);
            }
        });
    });

    // 儲存報告按鈕
    const saveBtn = containerElement.querySelector('#saveReportBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', handleSaveReport);
    }
}

/**
 * 返回總覽頁面
 */
function handleBackToSummary() {
    currentView = 'summary';
    window.scrollTo({ top: 0 });
    render();
}

// ==================== 各區塊渲染函式 ====================

/**
 * 智慧渲染按摩媒體（MP4/GIF）
 */
function renderMassageMedia(url, alt = '按摩示範') {
    if (!url) return '';

    const isImage = url.toLowerCase().endsWith('.gif') || url.toLowerCase().endsWith('.png');

    if (isImage) {
        return `
            <img
                src="${url}"
                alt="${alt}"
                class="massage-gif"
                loading="lazy"
                onerror="this.style.display='none'"
            >
        `;
    }

    return `
        <video
            class="massage-video"
            autoplay
            loop
            muted
            playsinline
            onerror="this.style.display='none'"
        >
            <source src="${url}" type="video/mp4">
            <p class="video-fallback">您的瀏覽器不支援影片播放</p>
        </video>
    `;
}

/**
 * 渲染臉部插圖（根據分數）
 */
function renderFaceIllustration(score) {
    const faceImage = score >= 85
        ? 'assets/icons/face-happy.svg'
        : 'assets/icons/face-neutral.svg';

    const faceAlt = score >= 85 ? '開心笑臉' : '微笑表情';

    return `
        <img
            src="${faceImage}"
            alt="${faceAlt}"
            class="face-illustration"
            onerror="this.style.display='none'"
        >
    `;
}

/**
 * 渲染 A 區：氣色分析
 */
function renderSectionA() {
    const data = resultData.sectionA || {};

    return `
        <div class="section-a">
            <!-- 使用者照片 -->
            <div class="photo-display">
                <img
                    src="${data.photoUrl || ''}"
                    alt="分析照片"
                    class="result-photo"
                    onerror="this.src='assets/icons/no-image.svg'"
                >
            </div>

            <!-- 活力氣色分數 -->
            <div class="circular-progress">
                <svg viewBox="0 0 160 160">
                    <defs>
                        <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#D4AF37;stop-opacity:1" />
                            <stop offset="50%" style="stop-color:#F0D875;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#D4AF37;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <circle class="progress-bg" cx="80" cy="80" r="70"></circle>
                    <circle
                        class="progress-bar"
                        cx="80"
                        cy="80"
                        r="70"
                        stroke-dasharray="440"
                        stroke-dashoffset="${440 - (440 * (data.score || 0) / 100)}"
                    ></circle>
                </svg>
                <div class="progress-content">
                    ${renderFaceIllustration(data.score || 0)}
                    <div class="progress-score">${data.score || 0}</div>
                    <div class="progress-label">氣色分數</div>
                </div>
            </div>

            <!-- 整體評價 -->
            <div class="evaluation-card">
                <h3 class="card-title">AI 氣色診斷</h3>
                <p class="evaluation-text">${data.evaluation || '暫無評價'}</p>
            </div>

            <!-- 按摩推薦 -->
            ${data.massages && data.massages.length > 0 ? `
                <div class="massage-card">
                    <h3 class="card-title">推薦按摩動作</h3>
                    <div class="massage-carousel">
                        <div class="massage-carousel-track">
                            ${data.massages.map((massage, index) => `
                                <div class="massage-item">
                                    ${renderMassageMedia(massage.gifUrl, massage.name || '按摩示範')}
                                    <div class="massage-info">
                                        <h4 class="massage-name">${massage.name || ''}</h4>
                                        <p class="massage-description">${massage.description || ''}</p>
                                        <p class="massage-effect"><strong>效果：</strong>${massage.effect || ''}</p>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="carousel-indicator">
                        ${data.massages.map((_, index) => `
                            <span class="indicator-dot ${index === 0 ? 'active' : ''}"></span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * 渲染 B 區：智能膚況解析
 */
function renderSectionB() {
    const data = resultData.sectionB || {};
    const topIssues = data.topIssues || [];

    return `
        <div class="section-b">
            <!-- 遮罩照片 -->
            <div class="photo-display">
                <img
                    src="${data.maskedPhotoUrl || ''}"
                    alt="膚況標註"
                    class="result-photo masked"
                    onerror="this.src='assets/icons/no-image.svg'"
                >
            </div>

            <!-- 雷達圖 -->
            <div class="radar-chart-wrapper">
                <h3 class="card-title">五角膚況分析</h3>
                <canvas id="radarChart" class="radar-chart"></canvas>
                <div class="score-legend">
                    <span class="legend-label">嚴重程度：</span>
                    <span class="legend-scale">
                        <span class="scale-item low">1 輕微</span>
                        <span class="scale-arrow">→</span>
                        <span class="scale-item high">5 嚴重</span>
                    </span>
                </div>
            </div>

            <!-- 兩大問題 - 簡潔列表 -->
            ${topIssues.length > 0 ? `
                <div class="top-issues">
                    <h3 class="card-title">主要問題</h3>
                    <div class="issues-simple-list">
                        ${topIssues.map((issue, index) => `
                            <div class="issue-simple-item">
                                <span class="issue-number">${index + 1}</span>
                                <div class="issue-info">
                                    <span class="issue-name">${issue.name || ''}</span>
                                    <span class="issue-desc">${issue.description || ''}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- 溫馨提示 -->
            <div class="warm-tip" role="note" aria-label="溫馨提示">
                <div class="tip-icon">
                    <img src="assets/icons/lightbulb.svg" alt="" class="icon" aria-hidden="true" width="24" height="24">
                </div>
                <div class="tip-content">
                    <p class="tip-text">別擔心！我們不只分析問題，接下來為您準備了專屬的改善建議和智慧配方，一起養好肌膚！</p>
                </div>
            </div>
        </div>
    `;
}

/**
 * 渲染 C 區：由內而外養膚
 */
function renderSectionC() {
    const data = resultData.sectionC || {};
    const suggestions = data.suggestions || [];

    return `
        <div class="section-c">
            ${suggestions.length > 0 ? `
                <div class="suggestions-simple-list">
                    ${suggestions.map((suggestion, index) => `
                        <div class="suggestion-simple-item">
                            <div class="suggestion-header">
                                <span class="suggestion-icon-mini">${getSuggestionIcon(suggestion.type)}</span>
                                <h4 class="suggestion-title">${suggestion.title || ''}</h4>
                            </div>
                            ${suggestion.ingredients ? `
                                <div class="suggestion-tags">
                                    ${suggestion.ingredients.map(ing => `<span class="suggestion-tag">${ing}</span>`).join('')}
                                </div>
                            ` : ''}
                            <p class="suggestion-text">${suggestion.content || ''}</p>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="empty-state">
                    <p>暫無生活建議</p>
                </div>
            `}
        </div>
    `;
}

/**
 * 取得建議類型圖示 HTML
 */
function getSuggestionIcon(type) {
    const iconPath = ICON_PATHS[type] || ICON_PATHS.lightbulb;
    return `<img src="${iconPath}" alt="" class="icon" aria-hidden="true" width="24" height="24">`;
}

/**
 * 渲染 D 區：智慧配方
 */
function renderSectionD() {
    const data = resultData.sectionD || {};
    const ingredients = data.ingredients || [];
    const products = data.products || [];
    const sensitivity = resultData.questionnaire?.answer3_tag || '';

    return `
        <div class="section-d">
            ${sensitivity === '輕度敏感' ? `
                <div class="sensitivity-notice" role="alert" aria-label="敏感肌膚提醒">
                    <div class="notice-icon">
                        <img src="assets/icons/warning.svg" alt="" class="icon" aria-hidden="true" width="24" height="24">
                    </div>
                    <div class="notice-content">
                        <h4>溫馨提醒</h4>
                        <p>您的肌膚偶爾會對新產品敏感，建議使用新產品前先在耳後或手腕內側進行小範圍測試，確認無不適後再使用於臉部。</p>
                    </div>
                </div>
            ` : ''}

            <!-- 推薦成分 - 膠囊標籤設計 -->
            ${ingredients.length > 0 ? `
                <div class="ingredients-section">
                    <h3 class="card-title">推薦成分</h3>
                    <p class="ingredients-intro">根據您的膚況分析，以下成分特別適合您，選購保養品時可以多留意成分表喔！</p>
                    <div class="ingredients-capsules">
                        ${ingredients.map((ing, index) => `
                            <div class="ingredient-capsule" style="animation-delay: ${index * 0.1}s">
                                <span class="capsule-icon">✦</span>
                                <div class="capsule-content">
                                    <span class="capsule-name">${ing.name || ''}</span>
                                    ${ing.description ? `<span class="capsule-desc">${ing.description}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- 成分與商品之間的過渡提示 -->
            ${ingredients.length > 0 && products.length > 0 ? `
                <div class="products-transition">
                    <div class="transition-icon">🎁</div>
                    <p class="transition-text">
                        不知道從哪裡開始？別擔心！<br>
                        我們已為您精選含有以上成分的優質產品 ↓
                    </p>
                </div>
            ` : ''}

            <!-- 商品推薦 -->
            <div class="products-section">
                <h3 class="card-title">商品推薦</h3>
                ${products.length > 0 ? `
                    <div class="products-carousel">
                        <div class="products-carousel-track">
                            ${products.map(product => renderProductCard(product)).join('')}
                        </div>
                    </div>
                    <div class="carousel-indicator">
                        ${products.map((_, index) => `
                            <span class="indicator-dot ${index === 0 ? 'active' : ''}"></span>
                        `).join('')}
                    </div>
                ` : `
                    <div class="empty-state">
                        <p>暫無商品推薦</p>
                    </div>
                `}
            </div>

            <!-- 保養小提醒 -->
            <div class="skincare-routine-reminder">
                <h3 class="card-title">日常保養小提醒</h3>
                <div class="routine-image-container" data-zoomable>
                    <img
                        src="assets/icons/skincare-routine.png?v=${Date.now()}"
                        alt="保養步驟：洗面乳 → 化妝水 → 精華液 → 乳液 → 面霜 → 眼霜 → 防曬"
                        class="routine-image"
                        loading="lazy"
                    >
                    <span class="zoom-hint">👆 點擊放大查看</span>
                </div>
                <p class="routine-tip">依照正確順序使用保養品，讓肌膚吸收更有效！</p>
            </div>
        </div>
    `;
}

/**
 * 渲染商品卡片
 */
function renderProductCard(product) {
    const buildMomoUrl = (brand, name) => {
        if (!brand || !name) return null;
        const keyword = encodeURIComponent(`${brand} ${name}`);
        return `https://www.momoshop.com.tw/search/searchShop.jsp?keyword=${keyword}`;
    };

    const momoUrl = buildMomoUrl(product.brand, product.name);

    return `
        <div class="product-card">
            <div class="product-image">
                <img
                    src="${product.imageUrl || ''}"
                    alt="${product.name || '商品圖片'}"
                    loading="lazy"
                    onerror="this.src='assets/icons/no-image.svg'"
                >
            </div>
            <div class="product-info">
                <div class="product-brand">${product.brand || ''}</div>
                <div class="product-name">${product.name || ''}</div>
                ${product.category || product.priceTier ? `
                    <div class="product-meta">
                        ${product.category ? `<span class="product-category">${product.category}</span>` : ''}
                        ${product.priceTier ? `<span class="product-price-tier">${product.priceTier}</span>` : ''}
                    </div>
                ` : ''}
                ${product.ingredients && product.ingredients.length > 0 ? `
                    <div class="product-ingredients">
                        ${product.ingredients.join('、')}
                    </div>
                ` : ''}
            </div>
            <div class="product-links">
                ${product.officialUrl ? `
                    <a href="${product.officialUrl}" target="_blank" rel="noopener" class="btn-link btn-official">
                        官網
                    </a>
                ` : ''}
                ${momoUrl ? `
                    <a href="${momoUrl}" target="_blank" rel="noopener" class="btn-link btn-momo">
                        MOMO
                    </a>
                ` : ''}
            </div>
        </div>
    `;
}

// ==================== 元件初始化 ====================

/**
 * 初始化按摩輪播
 */
function initMassageCarousel() {
    const carousel = containerElement.querySelector('.massage-carousel');
    if (!carousel) return;

    const instance = initCarousel(carousel, {
        trackSelector: '.massage-carousel-track',
        itemSelector: '.massage-item',
        indicatorSelector: '.massage-card .indicator-dot',
        gap: CONFIG.UI.CAROUSEL.GAP
    });

    if (instance) {
        carouselInstances.push(instance);
    }
}

/**
 * 初始化圓形進度環動畫
 */
function initCircularProgress() {
    const progressBar = containerElement.querySelector('.progress-bar');
    if (!progressBar) return;

    const targetOffset = progressBar.getAttribute('stroke-dashoffset');
    progressBar.style.strokeDashoffset = '440';

    setTimeout(() => {
        progressBar.style.strokeDashoffset = targetOffset;
    }, 100);
}

/**
 * 初始化產品輪播
 */
function initProductsCarousel() {
    const carousel = containerElement.querySelector('.products-carousel');
    if (!carousel) return;

    const instance = initCarousel(carousel, {
        trackSelector: '.products-carousel-track',
        itemSelector: '.product-card',
        indicatorSelector: '.products-section .indicator-dot',
        gap: CONFIG.UI.CAROUSEL.GAP
    });

    if (instance) {
        carouselInstances.push(instance);
    }
}

/**
 * 初始化返回頂部按鈕
 */
function initBackToTop() {
    const backToTopBtn = containerElement.querySelector('#backToTop');
    if (!backToTopBtn) return;

    // 監聽視窗滾動
    const handleScroll = () => {
        if (window.scrollY > CONFIG.RESULT.BACK_TO_TOP_THRESHOLD) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    };

    window.addEventListener('scroll', handleScroll);

    // 點擊返回頂部
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * 處理儲存報告
 */
function handleSaveReport() {
    // if (!isLiffLoggedIn()) {
    //     showToast('請在 LINE 中開啟此頁面', { type: 'warning' });
    //     return;
    // }

    // const flexMsg = buildAnalysisFlexMessage(resultData);
    // liff.shareTargetPicker([flexMsg])
    //     .then(() => showToast('分享成功！', { type: 'success' }))
    //     .catch(err => {
    //         console.error('分享失敗:', err);
    //         showToast('分享失敗，請稍後再試', { type: 'error' });
    //     });
    if (typeof liff !== 'undefined' && liff.isInClient()) {
        liff.closeWindow();
    } else {
        showToast('請在手機 LINE App 中開啟此頁面', { type: 'info' });
    }
}

// ==================== 匯出函式 ====================

export function getCurrentTab() {
    return currentTab;
}

export function setResultData(data) {
    resultData = data;
    if (containerElement) {
        render();
    }
}

export function getResultData() {
    return resultData;
}

export function goToTab(tab) {
    if (CONFIG.RESULT.TABS.includes(tab)) {
        currentView = 'detail';
        currentTab = tab;
        render();
        // 使用 requestAnimationFrame 確保 DOM 已更新
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                scrollToSection(tab);
            });
        });
    }
}

export function goToSummary() {
    currentView = 'summary';
    window.scrollTo({ top: 0 });
    render();
}

export function getCurrentView() {
    return currentView;
}
