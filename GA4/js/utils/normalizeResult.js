/**
 * 結果資料正規化模組
 * ======================================================
 * 將後端回傳的資料轉換為前端期望的格式
 * 確保欄位名稱、資料結構一致
 */

// 膚況問題的中英文對照（英文 → 中文）
const ISSUE_LABELS = {
    acne: '痘痘',
    comedone: '粉刺',
    darkCircle: '黑眼圈',
    spot: '斑點',
    wrinkle: '細紋'
};

// 膚況問題的中英文反向對照（中文 → 英文）
const ISSUE_LABELS_REVERSE = {
    '痘痘': 'acne',
    '粉刺': 'comedone',
    '黑眼圈': 'darkCircle',
    '斑點': 'spot',
    '斑': 'spot',  // 支援簡寫
    '細紋': 'wrinkle'
};

// 膚況問題的預設說明（當後端沒提供時使用）
const ISSUE_DESCRIPTIONS = {
    acne: '痘痘可能與油脂分泌旺盛、毛孔堵塞有關。建議保持肌膚清潔，使用含有水楊酸或茶樹成分的產品。',
    comedone: '粉刺通常出現在 T 字部位，與角質代謝有關。建議定期溫和去角質，使用含有果酸或杏仁酸的產品。',
    darkCircle: '黑眼圈可能與睡眠不足、用眼過度或血液循環不良有關。建議保持充足睡眠，使用含有維他命 C 或咖啡因的眼部產品。',
    spot: '斑點形成與紫外線曝曬、荷爾蒙變化有關。建議做好防曬，使用含有傳明酸或維他命 C 的美白產品。',
    wrinkle: '細紋與肌膚老化、膠原蛋白流失有關。建議加強保濕，使用含有 A 醇或胜肽的抗老產品。'
};

/**
 * 正規化 sectionB 的 scores
 * 將中文鍵值轉換為英文鍵值（如果需要）
 * @param {Object} scores - 後端回傳的 scores（可能是中文或英文鍵）
 * @returns {Object} 正規化後的 scores（英文鍵）
 */
function normalizeScores(scores) {
    if (!scores || typeof scores !== 'object') return {};

    const normalizedScores = {};

    // 遍歷所有鍵值
    Object.keys(scores).forEach(key => {
        // 如果是中文鍵，轉換為英文
        if (ISSUE_LABELS_REVERSE[key]) {
            const englishKey = ISSUE_LABELS_REVERSE[key];
            normalizedScores[englishKey] = scores[key];
            console.log(`🔄 轉換 scores 鍵值: "${key}" → "${englishKey}" = ${scores[key]}`);
        }
        // 如果已經是英文鍵，直接保留
        else if (ISSUE_LABELS[key]) {
            normalizedScores[key] = scores[key];
        }
        // 未知的鍵，也保留（向後相容）
        else {
            normalizedScores[key] = scores[key];
            console.warn(`⚠️ 未知的 scores 鍵值: "${key}"`);
        }
    });

    console.log('✅ 正規化後的 scores:', normalizedScores);
    return normalizedScores;
}

/**
 * 正規化 sectionB 的 topIssues
 * 將英文/中文 id 統一轉換為英文，name 轉換為中文，並補充缺少的欄位
 * @param {Array} topIssues - 後端回傳的 topIssues
 * @param {Object} scores - 已正規化的 scores（英文鍵）
 * @returns {Array} 正規化後的 topIssues
 */
function normalizeTopIssues(topIssues, scores = {}) {
    if (!Array.isArray(topIssues)) return [];

    return topIssues.map(issue => {
        const rawId = issue.id || issue.name; // 後端可能用 name 存 id

        // 🔥 將中文 id 轉換為英文（如果需要）
        let englishId = rawId;
        if (ISSUE_LABELS_REVERSE[rawId]) {
            englishId = ISSUE_LABELS_REVERSE[rawId];
            console.log(`🔄 轉換 topIssues id: "${rawId}" → "${englishId}"`);
        }

        // 取得中文名稱
        const chineseName = ISSUE_LABELS[englishId] || issue.name || rawId;

        // 從已正規化的 scores 中取得分數（使用英文 id）
        const score = scores[englishId] || issue.score || 0;

        // 取得說明
        const description = issue.description || ISSUE_DESCRIPTIONS[englishId] || '';

        return {
            id: englishId,        // 🔥 統一使用英文 id
            name: chineseName,    // 顯示用中文名稱
            score: score,
            description: description
        };
    });
}

/**
 * 正規化 sectionD 的 ingredients
 * 補充缺少的 description 欄位
 * @param {Array} ingredients - 後端回傳的 ingredients
 * @returns {Array} 正規化後的 ingredients
 */
function normalizeIngredients(ingredients) {
    if (!Array.isArray(ingredients)) return [];

    // 常見成分的預設說明
    const INGREDIENT_DESCRIPTIONS = {
        '菸鹼醯胺': '調節油脂分泌、縮小毛孔、提亮膚色',
        '甘草萃取': '舒緩鎮定、淡化色素沉澱',
        '水楊酸': '溫和代謝角質、深層清潔毛孔',
        '積雪草': '修護肌膚屏障、舒緩敏感',
        '果酸': '加速角質更新、改善膚質',
        '葡萄糖酸鋅': '調節皮脂、抗菌消炎',
        '茶樹精油': '天然抗菌、控油淨化',
        '綠茶萃取': '抗氧化、舒緩肌膚',
        '金縷梅萃取': '收斂毛孔、控油平衡',
        '維他命C': '抗氧化、提亮膚色、淡化黑眼圈',
        '玻尿酸': '高效保濕、維持肌膚彈性',
        '傳明酸': '抑制黑色素生成、淡化斑點',
        'A醇': '促進細胞更新、抗老淡紋',
        '胜肽': '緊緻肌膚、撫平細紋'
    };

    return ingredients.map(ing => ({
        name: ing.name || '',
        description: ing.description || INGREDIENT_DESCRIPTIONS[ing.name] || ''
    }));
}

/**
 * 正規化完整的結果資料
 * @param {Object} data - 後端回傳的原始 data
 * @returns {Object} 正規化後的 data
 */
export function normalizeResultData(data) {
    if (!data) return null;

    // 深拷貝避免修改原始資料
    const normalized = JSON.parse(JSON.stringify(data));

    // 正規化 sectionB（scores + topIssues）
    if (normalized.sectionB) {
        // 🔥 先轉換 scores 的鍵值（中文 → 英文）
        if (normalized.sectionB.scores) {
            normalized.sectionB.scores = normalizeScores(normalized.sectionB.scores);
        }

        // 再正規化 topIssues
        normalized.sectionB.topIssues = normalizeTopIssues(
            normalized.sectionB.topIssues,
            normalized.sectionB.scores
        );
    }

    // 正規化 sectionD.ingredients
    if (normalized.sectionD) {
        normalized.sectionD.ingredients = normalizeIngredients(
            normalized.sectionD.ingredients
        );
    }

    return normalized;
}

/**
 * 驗證結果資料是否完整
 * @param {Object} data - 結果資料
 * @returns {{ valid: boolean, missing: string[] }} 驗證結果
 */
export function validateResultData(data) {
    const missing = [];

    if (!data) {
        return { valid: false, missing: ['data'] };
    }

    // 檢查必要欄位
    if (!data.sectionA?.photoUrl) missing.push('sectionA.photoUrl');
    if (typeof data.sectionA?.score !== 'number') missing.push('sectionA.score');
    if (!data.sectionA?.evaluation) missing.push('sectionA.evaluation');

    if (!data.sectionB?.maskedPhotoUrl) missing.push('sectionB.maskedPhotoUrl');
    if (!data.sectionB?.scores) missing.push('sectionB.scores');

    // scores 的五個維度
    const requiredScores = ['acne', 'comedone', 'darkCircle', 'spot', 'wrinkle'];
    requiredScores.forEach(key => {
        if (typeof data.sectionB?.scores?.[key] !== 'number') {
            missing.push(`sectionB.scores.${key}`);
        }
    });

    return {
        valid: missing.length === 0,
        missing
    };
}