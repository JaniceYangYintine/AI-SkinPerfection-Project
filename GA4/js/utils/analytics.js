/**
 * analytics.js — GA4 / GTM 埋點模組（完全獨立，不修改任何其他檔案）
 * ======================================================
 * 追蹤項目：
 * 1. A/B/C/D 區塊停留時間：zone_view_start / zone_view_end
 * 2. 商品點擊率：product_click（官網 / MOMO 連結）
 * 3. 結果頁渲染完成：result_rendered
 *
 * 使用方式：在 index.html 加入 GTM script 後，引入此檔案即可
 * 不需要修改 result.js 或任何業務程式碼
 */

// ==================== dataLayer 推送 ====================

function dlPush(payload) {
    try {
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push(payload);
    } catch (e) {
        // 不讓追蹤影響主流程
    }
    // 開發環境 console 輸出，方便除錯
    console.log('[GTM]', payload.event, payload);
}

// ==================== 狀態管理 ====================

let dwellObserver = null;
let dwellTimers = new Map();
let isDwellTrackingActive = false;
let isProductClickBound = false;
let hasSentResultRendered = false;

// ==================== 1. A/B/C/D 區塊停留時間 ====================

function initDwellTracking() {
    if (isDwellTrackingActive) return;

    const sections = document.querySelectorAll('.detail-section[data-section]');
    if (!sections || sections.length === 0) return;

    isDwellTrackingActive = true;
    dwellTimers = new Map();

    dwellObserver = new IntersectionObserver((entries) => {
        const now = Date.now();

        entries.forEach((entry) => {
            const zone = (entry.target.dataset.section || '').toUpperCase();
            if (!['A', 'B', 'C', 'D'].includes(zone)) return;

            // 進入畫面（50% 以上可見）
            if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
                if (!dwellTimers.has(entry.target)) {
                    dwellTimers.set(entry.target, now);
                    dlPush({ event: 'zone_view_start', zone });
                }
            }

            // 離開畫面
            if (!entry.isIntersecting) {
                const start = dwellTimers.get(entry.target);
                if (start) {
                    dwellTimers.delete(entry.target);
                    const duration_ms = now - start;
                    dlPush({ event: 'zone_view_end', zone, duration_ms });
                }
            }
        });
    }, { threshold: [0, 0.5] });

    sections.forEach(sec => dwellObserver.observe(sec));
}

/**
 * 頁面關閉前，把還在計時的區段送出
 */
function flushDwellTimers() {
    const now = Date.now();
    try {
        dwellTimers.forEach((start, el) => {
            const zone = (el?.dataset?.section || '').toUpperCase();
            if (!['A', 'B', 'C', 'D'].includes(zone)) return;
            dlPush({ event: 'zone_view_end', zone, duration_ms: now - start });
        });
    } finally {
        dwellTimers.clear();
    }
}

// ==================== 2. 商品點擊（MOMO / 官網）====================

function initProductClickTracking() {
    if (isProductClickBound) return;
    isProductClickBound = true;

    // 事件委派：監聽整個 document，不需要等特定容器出現
    document.addEventListener('click', (evt) => {
        const link = evt.target.closest('a.btn-link');
        if (!link) return;

        const card = link.closest('.product-card');
        if (!card) return;

        // 判斷連結類型
        const link_type = link.classList.contains('btn-official')
            ? 'official'
            : link.classList.contains('btn-momo')
                ? 'momo'
                : 'other';

        // 產品資訊（從 DOM 抓，不需要 data 屬性）
        const product_name = (card.querySelector('.product-name')?.textContent || '').trim();
        const product_brand = (card.querySelector('.product-brand')?.textContent || '').trim();
        const click_url = link.getAttribute('href') || '';

        // 計算產品排序位置
        const productsSection = card.closest('.products-section');
        const allCards = productsSection
            ? Array.from(productsSection.querySelectorAll('.product-card'))
            : [];
        const rank = allCards.indexOf(card) + 1;

        dlPush({
            event: 'product_click',
            product_name,
            product_brand,
            rank,
            link_type,
            click_url
        });
    }, { capture: true });
}

// ==================== 3. 結果頁渲染完成 ====================

function sendResultRendered() {
    if (hasSentResultRendered) return;

    // 偵測是 summary 還是 detail view
    const detailView = document.querySelector('.detail-view');
    const summaryCard = document.querySelector('.summary-card');

    const view = detailView ? 'detail' : summaryCard ? 'summary' : 'unknown';

    // 如果是 detail view，抓當前 active tab
    let tab = '';
    if (detailView) {
        const activeTab = document.querySelector('.tab-btn.active');
        tab = activeTab?.dataset?.tab || '';
    }

    hasSentResultRendered = true;
    dlPush({ event: 'result_rendered', view, tab });
}

// ==================== 清理與重置 ====================

function cleanup() {
    if (dwellObserver) {
        dwellObserver.disconnect();
        dwellObserver = null;
    }
    flushDwellTimers();
    isDwellTrackingActive = false;
    hasSentResultRendered = false;
}

// ==================== DOM 監聽：自動偵測結果頁出現 ====================

function initMutationObserver() {
    const observer = new MutationObserver(() => {
        const sections = document.querySelectorAll('.detail-section[data-section]');

        // detail view 出現了
        if (sections.length > 0) {
            if (!isDwellTrackingActive) {
                // 清理舊的 observer 再重新綁
                if (dwellObserver) {
                    dwellObserver.disconnect();
                    dwellObserver = null;
                }
                dwellTimers.clear();
                isDwellTrackingActive = false;

                initDwellTracking();
                sendResultRendered();
            }
        } else {
            // detail view 被移除了（例如回到 summary），清理
            if (isDwellTrackingActive) {
                cleanup();
            }
        }

        // summary view 出現
        if (!hasSentResultRendered && document.querySelector('.summary-card')) {
            sendResultRendered();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
}

// ==================== 頁面離開時送出剩餘資料 ====================

window.addEventListener('pagehide', flushDwellTimers, { once: true });
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
        flushDwellTimers();
    }
});

// ==================== 初始化 ====================

initMutationObserver();
initProductClickTracking();
