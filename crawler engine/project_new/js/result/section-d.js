/**
 * D 區模組 - 產品推薦
 * 負責渲染成分說明和產品卡片
 */

// 成分圖示對應
const INGREDIENT_ICONS = {
    '咖啡因': '☕',
    '維生素C': '🍊',
    '維生素K': '💊',
    '煙醯胺': '✨',
    '熊果素': '🌿',
    '傳明酸': '💎',
    '玻尿酸': '💧',
    '視黃醇': '🌟',
    '水楊酸': '🧪',
    '杏仁酸': '🔬'
};

/**
 * 載入 D 區資料
 * @param {Object} result - 分析結果
 */
export function loadSectionD(result) {
    console.log('🚀 loadSectionD 開始執行...');

    const productRec = result?.d_product_recommendations;

    if (!productRec) {
        console.warn('⚠️ 沒有產品推薦資料,使用假資料');
        return;
    }

    // 渲染總覽頁的成分摘要
    if (productRec.ingredients?.length > 0) {
        renderIngredientsOverview(productRec.ingredients);
    }

    // 渲染詳情頁的成分說明
    if (productRec.ingredients?.length > 0) {
        renderIngredients(productRec.ingredients);
    }

    // 渲染產品卡片
    if (productRec.products?.length > 0) {
        renderProducts(productRec.products);
    }

    console.log('✅ loadSectionD 執行完成');
}

/**
 * 渲染總覽頁的成分摘要
 * @param {Array} ingredients - 成分列表
 */
export function renderIngredientsOverview(ingredients) {
    console.log('📝 開始渲染總覽頁成分摘要...', ingredients);

    const container = document.getElementById('ingredients-badges-overview');
    if (!container) {
        console.error('❌ 找不到總覽頁成分容器');
        return;
    }

    container.innerHTML = '';

    ingredients.forEach(ing => {
        const icon = INGREDIENT_ICONS[ing.primary_ingredient] || '💊';
        const badge = document.createElement('div');
        badge.className = 'ingredient-badge';
        badge.innerHTML = `
            <span class="ingredient-icon">${icon}</span>
            <span class="ingredient-text">針對${ing.issue_name}：${ing.primary_ingredient}</span>
        `;
        container.appendChild(badge);
    });

    console.log(`✅ 總覽頁成分摘要已渲染 (${ingredients.length} 個)`);
}

/**
 * 渲染詳情頁的成分說明
 * @param {Array} ingredients - 成分列表
 */
export function renderIngredients(ingredients) {
    console.log('📝 開始渲染詳情頁成分說明...', ingredients);

    // 動態生成成分說明卡片
    const detailSection = document.querySelector('[data-section="product_recommendation"] .detail-content');
    if (!detailSection) {
        console.error('❌ 找不到詳情頁成分容器');
        return;
    }

    // 找到標題後的位置
    const h2 = detailSection.querySelector('h2');
    if (!h2) return;

    // 移除舊的成分卡片
    const oldCards = detailSection.querySelectorAll('.ingredient-card-dynamic');
    oldCards.forEach(card => card.remove());

    // 插入新的成分卡片
    ingredients.forEach(ing => {
        const card = document.createElement('div');
        card.className = 'massage-card ingredient-card-dynamic';
        card.innerHTML = `
            <h3>針對${ing.issue_name}問題</h3>
            <p><strong>主攻手:</strong> ${ing.primary_ingredient}</p>
            <p style="font-size:13px; color:rgba(24,11,10,.70);">
                ${ing.description}
            </p>
        `;
        h2.insertAdjacentElement('afterend', card);
    });

    console.log(`✅ 詳情頁成分說明已渲染 (${ingredients.length} 個)`);
}

/**
 * 渲染產品卡片
 * @param {Array} products - 產品列表
 */
export function renderProducts(products) {
    console.log('📝 開始渲染產品卡片...', products);

    const container = document.getElementById('product-list');
    if (!container) {
        console.error('❌ 找不到產品列表容器');
        return;
    }

    container.innerHTML = '';

    products.forEach((product, index) => {
        const card = createProductCard(product, index);
        container.appendChild(card);
    });

    console.log(`✅ 已渲染 ${products.length} 個產品卡片`);
}

/**
 * 建立單個產品卡片
 * @param {Object} product - 產品資料
 * @param {number} index - 索引
 * @returns {HTMLElement} 產品卡片 DOM
 */
function createProductCard(product, index) {
    const card = document.createElement('div');
    card.className = 'product-card';

    // 成分標籤 HTML
    let ingredientTags = '';
    if (product.ingredients?.length > 0) {
        ingredientTags = product.ingredients.slice(0, 3).map(ing =>
            `<span class="ingredient-tag">${ing}</span>`
        ).join('');
    }

    card.innerHTML = `
        <img class="product-image" 
             src="${product.image_url || 'https://via.placeholder.com/240x180/D4A574/FFFFFF?text=Product'}" 
             alt="${product.name}"
             onerror="this.src='https://via.placeholder.com/240x180/D4A574/FFFFFF?text=No+Image'">
        <div class="product-info">
            <div class="product-brand">${product.brand || '品牌名稱'}</div>
            <div class="product-name">${product.name}</div>
            <div class="product-ingredients">
                ${ingredientTags || '<span class="ingredient-tag">成分資訊</span>'}
            </div>
            <div class="product-links">
                <a href="${product.product_url || '#'}" 
                   target="_blank" 
                   class="product-link"
                   onclick="trackProductClick(${product.id || index})">
                    前往官網 →
                </a>
                <a href="${product.momo_url || 'https://www.momoshop.com.tw/'}" 
                   target="_blank" 
                   class="product-link">
                    前往 momo →
                </a>
            </div>
        </div>
    `;

    return card;
}

/**
 * 追蹤產品點擊 (GA4)
 * @param {number} productId - 產品 ID
 */
export function trackProductClick(productId) {
    console.log('📊 追蹤產品點擊:', productId);

    // TODO: 實作 GA4 追蹤
    if (typeof gtag !== 'undefined') {
        gtag('event', 'product_click', {
            product_id: productId
        });
    }
}

// 暴露給全域 (供 HTML onclick 使用)
if (typeof window !== 'undefined') {
    window.trackProductClick = trackProductClick;
}
