/**
 * 資料載入模組
 * 負責從 API 或 localStorage 載入分析結果
 */

// API 配置
const API_CONFIG = {
    DEV_MODE: true,
    MOCK_URL: './api/mock_result.json',
    API_URL: 'https://your-api.run.app/api/result'
};

/**
 * 從 API 或 localStorage 載入結果
 * @returns {Promise<Object|null>} 分析結果
 */
export async function loadResultData() {
    console.log('🚀 開始載入結果資料...');

    try {
        // 1. 檢查是否有 session_id
        const sessionId = localStorage.getItem('session_id');

        if (!sessionId && !API_CONFIG.DEV_MODE) {
            console.warn('⚠️ 找不到 session_id,嘗試從 localStorage 讀取');
            return loadFromLocalStorage();
        }

        // 2. 從 API 取得結果
        console.log('📡 從 API 取得結果...', sessionId);

        const apiUrl = API_CONFIG.DEV_MODE
            ? API_CONFIG.MOCK_URL
            : `${API_CONFIG.API_URL}?session_id=${sessionId}`;

        const response = await fetch(apiUrl);

        if (!response.ok) {
            throw new Error(`API 回應錯誤: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ API 資料載入成功', result);

        return result;

    } catch (error) {
        console.error('❌ 從 API 載入失敗:', error);
        console.log('🔄 降級使用 localStorage 或 mock 資料');
        return loadFromLocalStorage();
    }
}

/**
 * 從 localStorage 讀取資料 (降級方案)
 * @returns {Object|null} 分析結果
 */
export function loadFromLocalStorage() {
    console.log('📦 從 localStorage 讀取資料...');

    const keys = ["result", "skinapp_result", "ai_result", "analysis_result"];
    for (const k of keys) {
        const raw = localStorage.getItem(k);
        if (raw) {
            try {
                const result = JSON.parse(raw);
                console.log(`✅ 從 localStorage.${k} 讀取成功`);
                return result;
            } catch (e) {
                console.error(`❌ 解析 localStorage.${k} 失敗:`, e);
            }
        }
    }

    console.warn('⚠️ localStorage 中沒有資料,將使用 HTML 中的假資料');
    return null;
}
