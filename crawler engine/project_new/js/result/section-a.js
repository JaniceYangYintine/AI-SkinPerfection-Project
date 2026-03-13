/**
 * A 區模組 - 氣色分析
 * 負責渲染 AI 診斷結果和按摩推薦
 */

// 行動推薦資料 (靜態資料)
const ACTION_RECOMMENDATIONS = [
    { id: 1, targetIssue: "眼周暗沉", actionName: "眼周穴道按摩", description: "透過眼周穴道按摩,促進血液循環,改善眼周暗沉", mediaType: "video", mediaUrl: "./assets/videos/actions/1.mp4" },
    { id: 2, targetIssue: "眼周浮腫", actionName: "眼周消腫按摩", description: "透過眼周消腫按摩,排除多餘水分,改善浮腫問題", mediaType: "video", mediaUrl: "./assets/videos/actions/2.mp4" },
    { id: 3, targetIssue: "臉部暗沉", actionName: "全臉提亮按摩", description: "透過全臉提亮按摩,促進新陳代謝,改善膚色暗沉", mediaType: "image", mediaUrl: "./assets/images/actions/3.png" },
    { id: 4, targetIssue: "肌膚乾燥", actionName: "保濕按摩手法", description: "透過保濕按摩手法,加強保養品吸收,改善乾燥問題", mediaType: "image", mediaUrl: "./assets/images/actions/4.png" },
    { id: 5, targetIssue: "法令紋明顯", actionName: "法令紋按摩", description: "透過法令紋按摩,放鬆嘴角肌肉,淡化法令紋", mediaType: "video", mediaUrl: "./assets/videos/actions/5.mp4" },
    { id: 6, targetIssue: "臉部線條鬆弛", actionName: "拉提按摩", description: "透過拉提按摩,緊緻臉部輪廓,改善鬆弛問題", mediaType: "video", mediaUrl: "./assets/videos/actions/6.mp4" },
    { id: 7, targetIssue: "肩頸僵硬", actionName: "肩頸放鬆運動", description: "透過肩頸放鬆運動,舒緩肌肉緊繃,改善血液循環", mediaType: "image", mediaUrl: "./assets/images/actions/7.png" },
    { id: 8, targetIssue: "壓力大", actionName: "深呼吸放鬆法", description: "透過深呼吸放鬆法,減輕壓力,恢復身心平衡", mediaType: "image", mediaUrl: "./assets/images/actions/8.png" },
    { id: 9, targetIssue: "睡眠品質差", actionName: "助眠穴道按摩", description: "透過助眠穴道按摩,改善睡眠品質,恢復肌膚活力", mediaType: "image", mediaUrl: "./assets/images/actions/9.png" },
    { id: 10, targetIssue: "氣色不佳", actionName: "臉部淋巴按摩", description: "透過臉部淋巴按摩,排除毒素,改善整體氣色", mediaType: "video", mediaUrl: "./assets/videos/actions/10.mp4" }
];

/**
 * 載入 A 區資料
 * @param {Object} result - 分析結果
 */
export function loadSectionA(result) {
    console.log('🚀 loadSectionA 開始執行...');

    // 載入使用者照片
    loadUserPhoto(result);

    // 渲染 AI 診斷摘要
    const summary = result?.a_diagnosis?.summary || result?.summary;
    if (summary) {
        const summaryEl = document.getElementById('ai-diagnosis-summary');
        if (summaryEl) {
            summaryEl.textContent = summary;
        }
    }

    // 渲染按摩推薦 (根據偵測到的問題)
    const detectedIssues = result?.a_diagnosis?.detectedIssues || result?.detectedIssues || [1, 2];
    renderMassageRecommendations(detectedIssues);

    console.log('✅ loadSectionA 執行完成');
}

/**
 * 載入使用者照片
 * @param {Object} result - 分析結果
 */
function loadUserPhoto(result) {
    // 優先從 localStorage 讀取 (Base64),否則從 result 讀取 URL
    const photoUrl = localStorage.getItem('user_photo')
        || result?.photo_url;

    if (!photoUrl) {
        console.warn('⚠️ 找不到使用者照片');
        return;
    }

    // 載入詳情頁照片
    const photoDetailEl = document.getElementById('user-photo-a');
    if (photoDetailEl) {
        photoDetailEl.src = photoUrl;
        photoDetailEl.style.display = 'block';
        console.log('✅ 詳情頁使用者照片已載入');
    }

    // 載入總覽頁照片
    const photoOverviewEl = document.getElementById('user-photo-overview');
    if (photoOverviewEl) {
        photoOverviewEl.src = photoUrl;
        photoOverviewEl.style.display = 'block';
        console.log('✅ 總覽頁使用者照片已載入');
    }
}

/**
 * 渲染按摩推薦
 * @param {Array} issueIds - 偵測到的問題 ID 列表
 */
function renderMassageRecommendations(issueIds) {
    console.log('📝 開始渲染按摩推薦:', issueIds);

    const container = document.getElementById('massage-list');
    if (!container) {
        console.error('❌ 找不到按摩推薦容器');
        return;
    }

    container.innerHTML = '';

    issueIds.forEach(id => {
        const action = ACTION_RECOMMENDATIONS.find(a => a.id === id);
        if (!action) return;

        const card = document.createElement('div');
        card.className = 'massage-card';

        const mediaHtml = action.mediaType === 'video'
            ? `<video src="${action.mediaUrl}" controls autoplay muted loop playsinline style="width:100%;border-radius:8px;"></video>`
            : `<img src="${action.mediaUrl}" alt="${action.actionName}" style="width:100%;border-radius:8px;">`;

        card.innerHTML = `
            <h3>${action.actionName}</h3>
            <p style="font-size:13px; color:rgba(24,11,10,.70); margin-bottom:12px;">${action.description}</p>
            ${mediaHtml}
        `;

        container.appendChild(card);
    });

    console.log(`✅ 已渲染 ${issueIds.length} 個按摩推薦`);
}
