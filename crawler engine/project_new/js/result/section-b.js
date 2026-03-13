/**
 * B 區模組 - 膚況分析
 * 負責渲染雷達圖和 Top 2 問題
 */

import { drawRadarChart } from '../components/radar-chart.js';

// 問題名稱對應
const ISSUE_NAMES = {
    spot: '斑',
    wrinkle: '皺紋',
    pore: '毛孔',
    acne: '痘痘',
    comedone: '粉刺'
};

// 嚴重度等級 (1-5 分制)
const SEVERITY_LEVELS = [
    { min: 1, max: 2, label: '輕微', color: '#4CAF50' },      // 1-2 分: 輕微
    { min: 2, max: 3.5, label: '中等', color: '#FF9800' },    // 2-3.5 分: 中等
    { min: 3.5, max: 5, label: '嚴重', color: '#F44336' }     // 3.5-5 分: 嚴重
];

/**
 * 載入 B 區資料
 * @param {Object} result - 分析結果
 */
export function loadSectionB(result) {
    console.log('🚀 loadSectionB 開始執行...');

    // 載入 AI 遮罩圖
    loadMaskPhoto(result);

    // 支援多種資料格式
    const skinScores = result?.b_skin_analysis?.scores
        || result?.skin_scores
        || result?.b_scores;

    const topIssues = result?.b_skin_analysis?.top_issues
        || result?.top_issues
        || result?.b_top_issues;

    // 繪製雷達圖 (如果有分數資料)
    if (skinScores) {
        drawRadarChart('skin-radar-detail', skinScores, 300);
        drawRadarChart('skin-radar-overview', skinScores, 150);
    } else {
        console.warn('⚠️ 沒有膚況分數資料,雷達圖將使用 HTML 預設');
    }

    // 渲染 Top 2 問題
    if (topIssues?.length > 0) {
        renderTopIssues(topIssues);
    }

    console.log('✅ loadSectionB 執行完成');
}

/**
 * 載入 AI 遮罩圖
 * @param {Object} result - 分析結果
 */
function loadMaskPhoto(result) {
    const maskEl = document.getElementById('annotated-photo');
    const loadingEl = document.getElementById('mask-loading');

    if (!maskEl) {
        console.warn('⚠️ 找不到 annotated-photo 元素');
        return;
    }

    // 從 localStorage 或 result 讀取遮罩圖
    const maskUrl = localStorage.getItem('mask_photo')
        || result?.b_skin_analysis?.mask_url
        || result?.mask_url;

    if (maskUrl) {
        // 隱藏 Loading,顯示圖片
        if (loadingEl) loadingEl.style.display = 'none';
        maskEl.src = maskUrl;
        maskEl.style.display = 'block';
        console.log('✅ AI 遮罩圖已載入');
    } else {
        // 保持 Loading 狀態 (等待後端回傳)
        console.log('⏳ 等待 AI 遮罩圖...');
    }
}

/**
 * 渲染 Top 2 問題
 * @param {Array} topIssues - Top 2 問題列表
 */
function renderTopIssues(topIssues) {
    console.log('📝 開始渲染 Top 2 問題:', topIssues);

    const container = document.getElementById('top-issues');
    if (!container) {
        console.error('❌ 找不到 Top Issues 容器');
        return;
    }

    container.innerHTML = '';

    topIssues.forEach((issue, index) => {
        const severity = getSeverityLevel(issue.score);

        const card = document.createElement('div');
        card.className = 'issue-card';
        card.innerHTML = `
            <div class="issue-header">
                <span class="issue-rank">#${index + 1}</span>
                <span class="issue-name">${issue.name}</span>
                <span class="issue-severity" style="background:${severity.color}">${severity.label}</span>
            </div>
            <div class="issue-score">
                <div class="score-bar">
                    <div class="score-fill" style="width:${issue.score * 20}%; background:${severity.color}"></div>
                </div>
                <span class="score-value">${issue.score.toFixed(1)}/5</span>
            </div>
            ${issue.llm_analysis ? `<p class="issue-analysis">${issue.llm_analysis}</p>` : ''}
        `;

        container.appendChild(card);
    });

    console.log(`✅ 已渲染 ${topIssues.length} 個 Top Issues`);
}

/**
 * 取得嚴重度等級
 * @param {number} score - 分數 (1-5)
 * @returns {Object} 嚴重度等級資訊
 */
function getSeverityLevel(score) {
    for (const level of SEVERITY_LEVELS) {
        if (score >= level.min && score < level.max) {
            return level;
        }
    }
    return SEVERITY_LEVELS[2]; // 預設嚴重
}
