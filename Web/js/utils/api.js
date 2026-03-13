/**
 * API 串接模組
 * 處理與後端 n8n 的所有通訊
 *
 * 自動切換：
 * - localhost → 使用 Mock 假資料
 * - 其他網域 → 使用真實 API
 */

import { CONFIG, ERROR_MESSAGES } from '../config.js';
import { IS_DEV } from '../env.js';
import { mockSubmitAnalysis, mockGetResult } from '../mock/mockData.js';

/**
 * 提交分析請求
 * @param {Blob} photoBlob - JPEG Blob
 * @param {Object} answers - 問卷答案
 * @returns {Promise<{success: boolean, session_id?: string, error?: string}>}
 */
export async function submitAnalysis(photoBlob, answers) {
    // 開發模式：使用 Mock
    if (IS_DEV) {
        console.log('🔧 [Mock] 使用假資料 - submitAnalysis');
        return await mockSubmitAnalysis();
    }

    // 正式環境：使用真實 API
    const url = `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.ANALYZE}`;
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.API.TIMEOUT);

        const formData = new FormData();
        const lineId = sessionStorage.getItem(CONFIG.STORAGE_KEYS.LINE_ID);

        formData.append('photo', photoBlob, 'photo.jpg');
        formData.append('answers', JSON.stringify(answers));
        if (lineId) {
            formData.append('line_id', lineId);
        }

        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.session_id) {
            return { success: true, session_id: data.session_id };
        } else {
            return { success: false, error: data.message || ERROR_MESSAGES.API_ERROR };
        }

    } catch (error) {
        console.error('submitAnalysis error:', error);

        if (error.name === 'AbortError') {
            return { success: false, error: ERROR_MESSAGES.API_TIMEOUT };
        }

        return { success: false, error: ERROR_MESSAGES.NETWORK_ERROR };
    }
}

/**
 * 輪詢取得分析結果
 * @param {string} sessionId - Session ID
 * @param {Function} onProgress - 進度回調（可選）
 * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
 */
export async function pollResult(sessionId, onProgress = null) {
    // 開發模式：使用 Mock
    if (IS_DEV) {
        console.log('🔧 [Mock] 使用假資料 - pollResult');
        return await mockGetResult((progress) => {
            if (onProgress) onProgress(progress);
        });
    }

    // 正式環境：使用真實 API
    const url = `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.RESULT}?session_id=${sessionId}`;
    const maxAttempts = CONFIG.API.TIMEOUT / CONFIG.API.POLL_INTERVAL;
    let attempts = 0;

    return new Promise((resolve) => {
        const poll = async () => {
            attempts++;

            // 回報進度
            if (onProgress) {
                onProgress(Math.min((attempts / maxAttempts) * 100, 99));
            }

            try {
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                // 分析完成
                if (data.status === 'completed' && data.data) {
                    resolve({ success: true, data: data.data });
                    return;
                }

                // 分析中，繼續輪詢
                if (data.status === 'processing' || data.status === 'pending') {
                    if (attempts >= maxAttempts) {
                        resolve({ success: false, error: ERROR_MESSAGES.API_TIMEOUT });
                        return;
                    }
                    setTimeout(poll, CONFIG.API.POLL_INTERVAL);
                    return;
                }

                // 分析失敗
                if (data.status === 'failed') {
                    resolve({ success: false, error: data.message || ERROR_MESSAGES.API_ERROR });
                    return;
                }

            } catch (error) {
                console.error('pollResult error:', error);

                // 重試機制
                if (attempts < maxAttempts) {
                    setTimeout(poll, CONFIG.API.POLL_INTERVAL);
                } else {
                    resolve({ success: false, error: ERROR_MESSAGES.NETWORK_ERROR });
                }
            }
        };

        poll();
    });
}

/**
 * 取得分析結果（單次請求）
 * @param {string} sessionId - Session ID
 * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
 */
export async function getResult(sessionId) {
    const url = `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.RESULT}?session_id=${sessionId}`;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.API.TIMEOUT);

        const response = await fetch(url, {
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'completed' && data.data) {
            return { success: true, data: data.data };
        } else if (data.status === 'processing' || data.status === 'pending') {
            return { success: false, error: '分析尚未完成', status: data.status };
        } else {
            return { success: false, error: data.message || ERROR_MESSAGES.API_ERROR };
        }

    } catch (error) {
        console.error('getResult error:', error);

        if (error.name === 'AbortError') {
            return { success: false, error: ERROR_MESSAGES.API_TIMEOUT };
        }

        return { success: false, error: ERROR_MESSAGES.NETWORK_ERROR };
    }
}
