/**
 * API 串接模組
 * 處理與後端 n8n 的所有通訊
 *
 * 自動切換：
 * - localhost → 使用 Mock 假資料
 * - 其他網域 → 使用真實 API
 */

import { CONFIG, ERROR_MESSAGES } from '../config.js';
// import { IS_DEV } from '../env.js';
// import { mockSubmitAnalysis, mockGetResult } from '../mock/mockData.js';
import { convertToAnswerTags } from './questionnaireMapping.js';
import { normalizeResultData, validateResultData } from './normalizeResult.js';

/**
 * 提交分析請求
 * @param {Blob} photoBlob - JPEG Blob
 * @param {Object} answers - 問卷答案
 * @returns {Promise<{success: boolean, session_id?: string, error?: string}>}
 */
export async function submitAnalysis(photoBlob, answers) {
    // 開發模式：使用 Mock
    // if (IS_DEV) {
    //     console.log('🔧 [Mock] 使用假資料 - submitAnalysis');
    //     return await mockSubmitAnalysis();
    // }

    // 正式環境：使用真實 API
    const url = `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.ANALYZE}`;
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.API.TIMEOUT);

        const formData = new FormData();
        const lineId = sessionStorage.getItem(CONFIG.STORAGE_KEYS.LINE_ID);

        // 將英文答案轉換為中文標籤
        const answerTags = convertToAnswerTags(answers);

        formData.append('photo', photoBlob, 'photo.jpg');
        formData.append('answers', JSON.stringify(answerTags));
        if (lineId) {
            formData.append('line_id', lineId);
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'ngrok-skip-browser-warning': 'true'
            },
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        console.log('📡 API Response status:', response.status);
        console.log('📡 API Response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const responseText = await response.text();
        console.log('📡 API Response raw:', responseText);

        let data;
        try {
            data = JSON.parse(responseText);
        } catch (parseError) {
            console.error('❌ JSON 解析失敗:', parseError);
            return { success: false, error: '伺服器回應格式錯誤' };
        }

        console.log('📡 API Response parsed:', data);

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
    // if (IS_DEV) {
    //     console.log('🔧 [Mock] 使用假資料 - pollResult');
    //     return await mockGetResult((progress) => {
    //         if (onProgress) onProgress(progress);
    //     });
    // }

    // 正式環境：使用真實 API
    const url = `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.RESULT}?session_id=${sessionId}`;
    const maxAttempts = Number.isFinite(CONFIG.API.MAX_POLL_ATTEMPTS)
        ? CONFIG.API.MAX_POLL_ATTEMPTS
        : Math.floor(CONFIG.API.TIMEOUT / CONFIG.API.POLL_INTERVAL);
    let attempts = 0;
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 5; // 連續錯誤上限

    console.log(`🔄 開始輪詢 session_id=${sessionId}, 最大嘗試次數=${maxAttempts}`);

    return new Promise((resolve) => {
        const poll = async () => {
            attempts++;

            // 回報進度
            if (onProgress) {
                onProgress(Math.min((attempts / maxAttempts) * 100, 99));
            }

            console.log(`🔄 輪詢 #${attempts}/${maxAttempts}...`);

            try {
                const response = await fetch(url, {
                    headers: {
                        'ngrok-skip-browser-warning': 'true'
                    }
                });

                console.log(`📡 輪詢回應 status=${response.status}`);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const responseText = await response.text();
                console.log(`📡 輪詢回應 raw (長度=${responseText.length}):`, responseText.substring(0, 500));

                // 檢查空回應
                if (!responseText || responseText.trim() === '') {
                    console.error('❌ 收到空白回應');
                    throw new Error('伺服器回傳空白回應');
                }

                let data;
                try {
                    data = JSON.parse(responseText);
                } catch (parseError) {
                    console.error('❌ JSON 解析失敗:', parseError);
                    console.error('❌ 原始內容:', responseText);
                    throw new Error(`JSON 解析失敗: ${responseText.substring(0, 100)}`);
                }

                // 重置連續錯誤計數
                consecutiveErrors = 0;

                console.log(`📡 輪詢狀態: ${data.status}`);

                // 分析完成
                if (data.status === 'completed' && data.data) {
                    console.log('✅ 分析完成！');

                    // 正規化資料（轉換中文、補充缺少欄位）
                    const normalizedData = normalizeResultData(data.data);

                    // 驗證資料完整性
                    const validation = validateResultData(normalizedData);
                    if (!validation.valid) {
                        console.warn('⚠️ 資料缺少欄位:', validation.missing);
                    }

                    // 🔥 檢查是否有 B、C、D 區資料（不只檢查物件存在，還要檢查內容）
                    const hasValidSectionB =
                        normalizedData.sectionB &&
                        normalizedData.sectionB.scores &&
                        (normalizedData.sectionB.scores.acne > 0 ||
                            normalizedData.sectionB.scores.comedone > 0 ||
                            normalizedData.sectionB.scores.darkCircle > 0 ||
                            normalizedData.sectionB.scores.spot > 0 ||
                            normalizedData.sectionB.scores.wrinkle > 0);

                    const hasValidSectionC =
                        normalizedData.sectionC &&
                        Array.isArray(normalizedData.sectionC.suggestions) &&
                        normalizedData.sectionC.suggestions.length > 0;

                    const hasValidSectionD =
                        normalizedData.sectionD &&
                        Array.isArray(normalizedData.sectionD.ingredients) &&
                        normalizedData.sectionD.ingredients.length > 0 &&
                        Array.isArray(normalizedData.sectionD.products) &&
                        normalizedData.sectionD.products.length > 0;

                    const hasAllSections =
                        normalizedData.sectionA &&
                        hasValidSectionB &&
                        hasValidSectionC &&
                        hasValidSectionD;

                    if (!hasAllSections) {
                        console.warn('⚠️ 資料尚未完整，繼續輪詢...');
                        console.log('📊 目前有的區塊:', {
                            A: !!normalizedData.sectionA,
                            B: hasValidSectionB,
                            C: hasValidSectionC,
                            D: hasValidSectionD
                        });
                        console.log('📊 詳細狀態:', {
                            'B.scores': normalizedData.sectionB?.scores,
                            'C.suggestions.length': normalizedData.sectionC?.suggestions?.length,
                            'D.ingredients.length': normalizedData.sectionD?.ingredients?.length,
                            'D.products.length': normalizedData.sectionD?.products?.length
                        });

                        // 繼續輪詢
                        if (attempts < maxAttempts) {
                            setTimeout(poll, CONFIG.API.POLL_INTERVAL);
                            return;
                        } else {
                            console.log('⏰ 達到最大嘗試次數，但資料不完整');
                            resolve({ success: false, error: '分析資料不完整，請稍後重試' });
                            return;
                        }
                    }

                    console.log('📦 正規化後資料:', normalizedData);
                    console.log('🔍 資料結構檢查:', {
                        hasA: !!normalizedData.sectionA,
                        hasB: !!normalizedData.sectionB,
                        hasC: !!normalizedData.sectionC,
                        hasD: !!normalizedData.sectionD,
                        sectionA_keys: normalizedData.sectionA ? Object.keys(normalizedData.sectionA) : [],
                        sectionB_keys: normalizedData.sectionB ? Object.keys(normalizedData.sectionB) : [],
                        sectionC_keys: normalizedData.sectionC ? Object.keys(normalizedData.sectionC) : [],
                        sectionD_keys: normalizedData.sectionD ? Object.keys(normalizedData.sectionD) : []
                    });
                    resolve({ success: true, data: normalizedData });
                    return;
                }

                // 分析中，繼續輪詢
                if (data.status === 'processing' || data.status === 'pending') {
                    if (attempts >= maxAttempts) {
                        console.log('⏰ 達到最大嘗試次數，超時');
                        resolve({ success: false, error: ERROR_MESSAGES.API_TIMEOUT });
                        return;
                    }
                    setTimeout(poll, CONFIG.API.POLL_INTERVAL);
                    return;
                }

                // 分析失敗
                if (data.status === 'failed') {
                    console.log('❌ 分析失敗:', data.message);
                    resolve({ success: false, error: data.message || ERROR_MESSAGES.API_ERROR });
                    return;
                }

                // 未知狀態，視為失敗（避免無限輪詢）
                console.log('❓ 未知狀態:', data.status);
                resolve({
                    success: false,
                    error: `未知的分析狀態: ${data.status || '無狀態'}`
                });
                return;

            } catch (error) {
                consecutiveErrors++;
                console.error(`❌ 輪詢錯誤 #${consecutiveErrors}:`, error.message);

                // 如果連續錯誤太多，直接失敗
                if (consecutiveErrors >= maxConsecutiveErrors) {
                    console.error('❌ 連續錯誤過多，停止輪詢');
                    resolve({ success: false, error: ERROR_MESSAGES.NETWORK_ERROR });
                    return;
                }

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
            headers: {
                'ngrok-skip-browser-warning': 'true'
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'completed' && data.data) {
            // 正規化資料
            const normalizedData = normalizeResultData(data.data);
            return { success: true, data: normalizedData };
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
