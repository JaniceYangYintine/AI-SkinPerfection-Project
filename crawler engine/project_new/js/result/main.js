/**
 * Result 頁面主入口
 * 協調所有模組的載入和渲染
 */

import { loadResultData } from './data-loader.js';
import { loadSectionA } from './section-a.js';
import { loadSectionB } from './section-b.js';
import { loadSectionC } from './section-c.js';
import { loadSectionD, trackProductClick } from './section-d.js';

// ================== 頁面狀態 ==================
let currentSection = 'overview';
let sectionStartTime = Date.now();

// ================== 初始化 ==================

/**
 * 頁面初始化
 */
async function init() {
    console.log('🚀 Result 頁面初始化...');

    try {
        // 載入結果資料
        const result = await loadResultData();

        if (result) {
            // 載入各區塊
            loadSectionA(result);
            loadSectionB(result);
            loadSectionC(result);
            loadSectionD(result);

            console.log('✅ 所有區塊載入完成');
        } else {
            console.warn('⚠️ 沒有結果資料,使用 HTML 中的預設內容');
        }

    } catch (error) {
        console.error('❌ 初始化失敗:', error);
    }
}

// ================== 頁面切換功能 ==================

/**
 * 顯示詳情頁
 * @param {string} sectionKey - 區塊 key
 */
function showDetail(sectionKey) {
    console.log('📖 顯示詳情:', sectionKey);

    // 隱藏總覽頁
    const overview = document.getElementById('overview-container');
    if (overview) overview.style.display = 'none';

    // 隱藏所有詳情頁
    document.querySelectorAll('.detail-section').forEach(section => {
        section.style.display = 'none';
    });

    // 顯示指定詳情頁
    const detail = document.querySelector(`.detail-section[data-section="${sectionKey}"]`);
    if (detail) {
        detail.style.display = 'block';
        detail.scrollTop = 0;
    }

    // 追蹤區塊切換
    trackSectionStart(sectionKey);
    currentSection = sectionKey;
}

/**
 * 返回總覽頁
 */
function backToOverview() {
    console.log('🔙 返回總覽');

    // 追蹤區塊結束
    trackSectionEnd(currentSection);

    // 隱藏所有詳情頁
    document.querySelectorAll('.detail-section').forEach(section => {
        section.style.display = 'none';
    });

    // 顯示總覽頁
    const overview = document.getElementById('overview-container');
    if (overview) overview.style.display = 'block';

    currentSection = 'overview';
}

/**
 * 儲存到 LINE
 */
function saveToLine() {
    console.log('💾 儲存到 LINE');
    alert('功能開發中...');
}

// ================== GA4 追蹤 ==================

/**
 * 追蹤區塊開始
 * @param {string} section - 區塊名稱
 */
function trackSectionStart(section) {
    sectionStartTime = Date.now();
    console.log('📊 開始追蹤:', section);

    if (typeof gtag !== 'undefined') {
        gtag('event', 'section_view', {
            section_name: section
        });
    }
}

/**
 * 追蹤區塊結束
 * @param {string} section - 區塊名稱
 */
function trackSectionEnd(section) {
    const duration = (Date.now() - sectionStartTime) / 1000;
    console.log('📊 結束追蹤:', section, `(${duration.toFixed(1)}s)`);

    if (typeof gtag !== 'undefined') {
        gtag('event', 'section_leave', {
            section_name: section,
            duration_seconds: duration
        });
    }
}

// ================== 暴露全域函數 ==================
// 供 HTML onclick 使用
window.showDetail = showDetail;
window.backToOverview = backToOverview;
window.saveToLine = saveToLine;
window.trackProductClick = trackProductClick;

// ================== 頁面載入 ==================
window.addEventListener('DOMContentLoaded', init);

console.log('📦 Result 模組已載入');
