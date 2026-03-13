/**
 * 總覽頁模組
 * ======================================================
 * 從完整分析結果中提取摘要，顯示四大區塊的重點資訊
 * 點擊「查看詳情」直接切換到對應 Tab，不需重新呼叫 API
 *
 * 設計原則：
 * 1. 資料來源：使用已載入的 resultData，不額外呼叫 API
 * 2. 單一職責：只負責摘要的提取與渲染
 * 3. 鬆耦合：透過 callback 與 result.js 互動
 */

import { CONFIG } from '../config.js';

// ==================== 模組常數 ====================

/**
 * 分數對應星級（0-100 分對應 1-5 星）
 */
const SCORE_TO_STARS = [
    { min: 85, stars: 5 },
    { min: 70, stars: 4 },
    { min: 55, stars: 3 },
    { min: 40, stars: 2 },
    { min: 0, stars: 1 }
];

/**
 * 分數對應評語
 */
const SCORE_LABELS = {
    5: '非常好',
    4: '良好',
    3: '一般',
    2: '需改善',
    1: '需注意'
};

// ==================== 資料提取函式 ====================

/**
 * 從完整資料中提取總覽摘要
 * @param {Object} resultData - 完整的分析結果資料
 * @returns {Object} 摘要資料
 */
export function extractSummary(resultData) {
    if (!resultData) return null;

    return {
        // 分析時間
        analyzedAt: new Date().toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }),

        // Section A 摘要
        sectionA: extractSectionASummary(resultData.sectionA),

        // Section B 摘要
        sectionB: extractSectionBSummary(resultData.sectionB),

        // Section C 摘要
        sectionC: extractSectionCSummary(resultData.sectionC),

        // Section D 摘要
        sectionD: extractSectionDSummary(resultData.sectionD)
    };
}

/**
 * 提取 A 區摘要：氣色分數、星級、主要按摩建議
 */
function extractSectionASummary(sectionA) {
    if (!sectionA) return { score: 0, stars: 1, label: '無資料', massageNames: [] };

    const score = sectionA.score || 0;
    const stars = getStarsFromScore(score);
    const label = SCORE_LABELS[stars];

    // 取前 2 個按摩動作名稱
    const massageNames = (sectionA.massages || [])
        .slice(0, 2)
        .map(m => m.name)
        .filter(Boolean);

    return { score, stars, label, massageNames };
}

/**
 * 提取 B 區摘要：前兩大膚況問題
 */
function extractSectionBSummary(sectionB) {
    if (!sectionB) return { topIssues: [], hasScores: false };

    const scores = sectionB.scores || {};
    const hasScores = Object.values(scores).some(v => v > 0);

    // 從 topIssues 取前 2 個，包含名稱和分數
    const topIssues = (sectionB.topIssues || [])
        .slice(0, 2)
        .map(issue => ({
            name: issue.name || '',
            score: issue.score || scores[issue.id] || 0
        }))
        .filter(issue => issue.name);

    return { topIssues, hasScores };
}

/**
 * 提取 C 區摘要：建議數量和標題列表
 */
function extractSectionCSummary(sectionC) {
    if (!sectionC) return { count: 0, titles: [] };

    const suggestions = sectionC.suggestions || [];

    return {
        count: suggestions.length,
        titles: suggestions.map(s => s.title).filter(Boolean)
    };
}

/**
 * 提取 D 區摘要：推薦成分（前 5 個）和商品數量
 */
function extractSectionDSummary(sectionD) {
    if (!sectionD) return { ingredientNames: [], productCount: 0 };

    const ingredients = sectionD.ingredients || [];
    const products = sectionD.products || [];

    return {
        ingredientNames: ingredients.slice(0, 5).map(i => i.name).filter(Boolean),
        ingredientTotal: ingredients.length,
        productCount: products.length
    };
}

// ==================== 渲染函式 ====================

/**
 * 渲染總覽頁面
 * @param {Object} summaryData - 摘要資料（由 extractSummary 產生）
 * @param {Function} onViewDetail - 點擊「查看詳情」的 callback，傳入 tab 名稱
 * @returns {string} HTML 字串
 */
export function renderSummary(summaryData, onViewDetail) {
    if (!summaryData) {
        return '<div class="summary-error">無法載入分析摘要</div>';
    }

    return `
        <div class="summary-wrapper">
            <!-- 標題區 -->
            <header class="summary-header">
                <h2 class="summary-title">您的分析結果</h2>
                <time class="summary-time">${summaryData.analyzedAt}</time>
            </header>

            <!-- 四大區塊卡片 -->
            <div class="summary-cards">
                ${renderSectionACard(summaryData.sectionA)}
                ${renderSectionBCard(summaryData.sectionB)}
                ${renderSectionCCard(summaryData.sectionC)}
                ${renderSectionDCard(summaryData.sectionD)}
            </div>
        </div>
    `;
}

/**
 * 渲染 A 區卡片：活力氣色指南
 */
function renderSectionACard(data) {
    const starsHtml = renderStars(data.stars);
    const massageList = data.massageNames.length > 0
        ? data.massageNames.map(name => `<li>${name}</li>`).join('')
        : '<li>暫無建議</li>';

    return `
        <article class="summary-card summary-card-a" data-section="A">
            <div class="card-header">
                <span class="card-badge">A 區</span>
                <h3 class="card-title">活力氣色指南</h3>
            </div>

            <div class="card-body">
                <div class="score-display">
                    <span class="score-value">${data.score}</span>
                    <div class="score-meta">
                        <span class="score-stars">${starsHtml}</span>
                        <span class="score-label">${data.label}</span>
                    </div>
                </div>

                <div class="card-info">
                    <p class="info-label">主要建議：</p>
                    <ul class="info-list">
                        ${massageList}
                    </ul>
                </div>
            </div>

            <button class="card-action" data-tab="A">
                查看詳情 <span class="arrow">→</span>
            </button>
        </article>
    `;
}

/**
 * 渲染 B 區卡片：智能膚況解析
 */
function renderSectionBCard(data) {
    const issuesHtml = data.topIssues.length > 0
        ? data.topIssues.map(issue => `
            <div class="issue-item">
                <span class="issue-name">${issue.name}</span>
                <span class="issue-score">${renderScoreDots(issue.score)} ${issue.score} 分</span>
            </div>
        `).join('')
        : '<p class="no-issues">膚況良好，無明顯問題</p>';

    const needAttention = data.topIssues.length > 0
        ? `需要關注：${data.topIssues.map(i => i.name).join('、')}`
        : '整體膚況健康';

    return `
        <article class="summary-card summary-card-b" data-section="B">
            <div class="card-header">
                <span class="card-badge">B 區</span>
                <h3 class="card-title">智能膚況解析</h3>
            </div>

            <div class="card-body">
                <div class="issues-display">
                    <p class="info-label">膚況分數：</p>
                    ${issuesHtml}
                </div>

                <p class="attention-text">${needAttention}</p>
            </div>

            <button class="card-action" data-tab="B">
                查看詳情 <span class="arrow">→</span>
            </button>
        </article>
    `;
}

/**
 * 渲染 C 區卡片：由內而外養膚
 */
function renderSectionCCard(data) {
    const titlesList = data.titles.length > 0
        ? data.titles.map(title => `<li>${title}</li>`).join('')
        : '<li>暫無建議</li>';

    return `
        <article class="summary-card summary-card-c" data-section="C">
            <div class="card-header">
                <span class="card-badge">C 區</span>
                <h3 class="card-title">由內而外養膚</h3>
            </div>

            <div class="card-body">
                <p class="info-label">${data.count} 組飲食建議：</p>
                <ul class="info-list">
                    ${titlesList}
                </ul>
            </div>

            <button class="card-action" data-tab="C">
                查看詳情 <span class="arrow">→</span>
            </button>
        </article>
    `;
}

/**
 * 渲染 D 區卡片：智慧配方
 */
function renderSectionDCard(data) {
    const ingredientTags = data.ingredientNames.length > 0
        ? data.ingredientNames.map(name => `<span class="ingredient-tag">${name}</span>`).join('')
        : '<span class="no-data">暫無推薦</span>';

    const moreCount = data.ingredientTotal - data.ingredientNames.length;
    const moreText = moreCount > 0 ? `<span class="more-tag">+${moreCount}</span>` : '';

    return `
        <article class="summary-card summary-card-d" data-section="D">
            <div class="card-header">
                <span class="card-badge">D 區</span>
                <h3 class="card-title">智慧配方</h3>
            </div>

            <div class="card-body">
                <div class="ingredients-preview">
                    <p class="info-label">推薦成分：</p>
                    <div class="tags-container">
                        ${ingredientTags}
                        ${moreText}
                    </div>
                </div>

                <p class="products-count">產品推薦：${data.productCount} 個</p>
            </div>

            <button class="card-action" data-tab="D">
                查看詳情 <span class="arrow">→</span>
            </button>
        </article>
    `;
}

// ==================== 輔助函式 ====================

/**
 * 分數轉星級
 */
function getStarsFromScore(score) {
    for (const level of SCORE_TO_STARS) {
        if (score >= level.min) return level.stars;
    }
    return 1;
}

/**
 * 渲染星星
 */
function renderStars(count) {
    const filled = '★'.repeat(count);
    const empty = '☆'.repeat(5 - count);
    return `<span class="stars">${filled}${empty}</span>`;
}

/**
 * 渲染分數點（用於膚況分數顯示）
 */
function renderScoreDots(score) {
    const maxScore = 5;
    const filled = Math.min(Math.round(score), maxScore);
    const filledDots = '<span class="dot filled">●</span>'.repeat(filled);
    const emptyDots = '<span class="dot empty">○</span>'.repeat(maxScore - filled);
    return `<span class="score-dots">${filledDots}${emptyDots}</span>`;
}

// ==================== 事件綁定 ====================

/**
 * 綁定總覽頁事件
 * @param {HTMLElement} container - 容器元素
 * @param {Function} onViewDetail - 點擊「查看詳情」的 callback
 */
export function bindSummaryEvents(container, onViewDetail) {
    if (!container || typeof onViewDetail !== 'function') return;

    // 使用事件委派，只綁定一個 listener
    container.addEventListener('click', (e) => {
        const actionBtn = e.target.closest('.card-action');
        if (actionBtn) {
            const tab = actionBtn.dataset.tab;
            if (tab) {
                onViewDetail(tab);
            }
        }
    });
}
