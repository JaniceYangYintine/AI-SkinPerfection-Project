/**
 * 結果頁模組
 * 處理分析結果的顯示、Tab 切換、各區塊渲染
 */

import { CONFIG } from '../config.js';
import { drawRadarChartWithValues } from './radar.js';

// 模組狀態
let resultData = null;
let currentTab = CONFIG.RESULT.DEFAULT_TAB;
let containerElement = null;

/**
 * 初始化結果頁模組
 * @param {HTMLElement} container - 容器元素
 * @param {Object} data - 後端回傳的結果資料
 */
export function initResult(container, data) {
    containerElement = container;
    resultData = data;
    currentTab = CONFIG.RESULT.DEFAULT_TAB;

    renderResult();
}

/**
 * 渲染結果頁
 */
function renderResult() {
    if (!containerElement || !resultData) return;

    containerElement.innerHTML = `
        <div class="result-wrapper">
            <!-- Tab 切換 -->
            <div class="tab-nav">
                ${CONFIG.RESULT.TABS.map(tab => `
                    <button
                        class="tab-btn ${tab === currentTab ? 'active' : ''}"
                        data-tab="${tab}"
                    >
                        ${getTabLabel(tab)}
                    </button>
                `).join('')}
            </div>

            <!-- Tab 內容 -->
            <div class="tab-content">
                ${renderTabContent(currentTab)}
            </div>

            <!-- 儲存報告按鈕 -->
            <div class="result-actions">
                <button class="btn btn-primary btn-save-report" id="saveReportBtn">
                    儲存報告並分享
                </button>
            </div>
        </div>
    `;

    // 綁定事件
    bindResultEvents();

    // 繪製雷達圖（如果在 B 區）
    if (currentTab === 'B') {
        const radarCanvas = containerElement.querySelector('#radarChart');
        if (radarCanvas && resultData.sectionB?.scores) {
            drawRadarChartWithValues(radarCanvas, resultData.sectionB.scores);
        }
    }
}

/**
 * 取得 Tab 標籤名稱
 */
function getTabLabel(tab) {
    const labels = {
        'A': 'A 氣色',
        'B': 'B 膚況',
        'C': 'C 生活建議',
        'D': 'D 產品推薦'
    };
    return labels[tab] || tab;
}

/**
 * 渲染 Tab 內容
 */
function renderTabContent(tab) {
    switch (tab) {
        case 'A':
            return renderSectionA();
        case 'B':
            return renderSectionB();
        case 'C':
            return renderSectionC();
        case 'D':
            return renderSectionD();
        default:
            return '<div class="error">未知的區塊</div>';
    }
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
                    onerror="this.src='assets/images/no-image.svg'"
                >
            </div>

            <!-- 氣色分數 -->
            <div class="score-circle">
                <div class="score-value">${data.score || 0}</div>
                <div class="score-label">氣色分數</div>
            </div>

            <!-- 整體評價 -->
            <div class="evaluation-card">
                <h3 class="card-title">整體評價</h3>
                <p class="evaluation-text">${data.evaluation || '暫無評價'}</p>
            </div>

            <!-- 按摩推薦 -->
            ${data.massage ? `
                <div class="massage-card">
                    <h3 class="card-title">推薦按摩動作</h3>
                    <div class="massage-content">
                        <img
                            src="${data.massage.gifUrl || ''}"
                            alt="按摩示範"
                            class="massage-gif"
                            onerror="this.style.display='none'"
                        >
                        <div class="massage-info">
                            <h4 class="massage-name">${data.massage.name || ''}</h4>
                            <p class="massage-description">${data.massage.description || ''}</p>
                            <p class="massage-effect"><strong>效果：</strong>${data.massage.effect || ''}</p>
                        </div>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * 渲染 B 區：膚況分析
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
                    onerror="this.src='assets/images/no-image.svg'"
                >
            </div>

            <!-- 雷達圖 -->
            <div class="radar-chart-wrapper">
                <h3 class="card-title">五角膚況分析</h3>
                <canvas id="radarChart" class="radar-chart"></canvas>
            </div>

            <!-- 兩大問題 -->
            ${topIssues.length > 0 ? `
                <div class="top-issues">
                    <h3 class="card-title">主要問題</h3>
                    <div class="issues-list">
                        ${topIssues.map((issue, index) => `
                            <div class="issue-card">
                                <div class="issue-rank">${index + 1}</div>
                                <div class="issue-content">
                                    <h4 class="issue-name">${issue.name || ''}</h4>
                                    <p class="issue-description">${issue.description || ''}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * 渲染 C 區：生活建議
 */
function renderSectionC() {
    const data = resultData.sectionC || {};
    const suggestions = data.suggestions || [];

    return `
        <div class="section-c">
            <h3 class="section-title">由內而外養膚</h3>

            <div class="suggestions-list">
                ${suggestions.map((suggestion, index) => `
                    <div class="suggestion-card">
                        <div class="suggestion-icon">${getSuggestionIcon(suggestion.type)}</div>
                        <div class="suggestion-content">
                            <h4 class="suggestion-title">${suggestion.title || ''}</h4>
                            <p class="suggestion-text">${suggestion.content || ''}</p>
                        </div>
                    </div>
                `).join('')}
            </div>

            ${suggestions.length === 0 ? `
                <div class="empty-state">
                    <p>暫無生活建議</p>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * 取得建議類型圖示
 */
function getSuggestionIcon(type) {
    const icons = {
        'diet': '🥗',
        'sleep': '😴',
        'exercise': '🏃',
        'stress': '🧘',
        'skincare': '✨'
    };
    return icons[type] || '💡';
}

/**
 * 渲染 D 區：產品推薦
 */
function renderSectionD() {
    const data = resultData.sectionD || {};
    const ingredients = data.ingredients || [];
    const products = data.products || [];

    return `
        <div class="section-d">
            <!-- 推薦成分 -->
            ${ingredients.length > 0 ? `
                <div class="ingredients-section">
                    <h3 class="section-title">推薦成分</h3>
                    <div class="ingredients-list">
                        ${ingredients.map(ing => `
                            <div class="ingredient-tag">
                                <span class="ingredient-name">${ing.name || ''}</span>
                                ${ing.description ? `<span class="ingredient-desc">${ing.description}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- 商品推薦 -->
            <div class="products-section">
                <h3 class="section-title">商品推薦</h3>
                <div class="products-grid">
                    ${products.map(product => renderProductCard(product)).join('')}
                </div>
            </div>

            ${products.length === 0 ? `
                <div class="empty-state">
                    <p>暫無商品推薦</p>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * 渲染商品卡片
 */
function renderProductCard(product) {
    return `
        <div class="product-card">
            <div class="product-image">
                <img
                    src="${product.imageUrl || ''}"
                    alt="${product.name || '商品圖片'}"
                    loading="lazy"
                    onerror="this.src='assets/images/no-image.svg'"
                >
            </div>
            <div class="product-info">
                <div class="product-brand">${product.brand || ''}</div>
                <div class="product-name">${product.name || ''}</div>
                ${product.ingredients && product.ingredients.length > 0 ? `
                    <div class="product-ingredients">
                        含有：${product.ingredients.join('、')}
                    </div>
                ` : ''}
            </div>
            <div class="product-links">
                ${product.officialUrl ? `
                    <a href="${product.officialUrl}" target="_blank" rel="noopener" class="btn-link btn-official">
                        官網
                    </a>
                ` : ''}
                ${product.momoUrl ? `
                    <a href="${product.momoUrl}" target="_blank" rel="noopener" class="btn-link btn-momo">
                        MOMO
                    </a>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * 綁定結果頁事件
 */
function bindResultEvents() {
    // Tab 切換
    const tabBtns = containerElement.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tab = e.target.dataset.tab;
            if (tab && tab !== currentTab) {
                switchTab(tab);
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
 * 切換 Tab
 */
function switchTab(tab) {
    currentTab = tab;
    renderResult();
}

/**
 * 處理儲存報告
 */
function handleSaveReport() {
    // TODO: 整合 LINE 分享功能
    alert('報告已儲存！\n（LINE 分享功能開發中）');
}

/**
 * 取得目前 Tab
 */
export function getCurrentTab() {
    return currentTab;
}

/**
 * 設定結果資料
 */
export function setResultData(data) {
    resultData = data;
    if (containerElement) {
        renderResult();
    }
}

/**
 * 取得結果資料
 */
export function getResultData() {
    return resultData;
}

/**
 * 外部切換 Tab
 */
export function goToTab(tab) {
    if (CONFIG.RESULT.TABS.includes(tab)) {
        switchTab(tab);
    }
}
