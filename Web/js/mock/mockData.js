/**
 * Mock 假資料
 * 用於前端開發測試，後端完成後自動切換為真實 API
 */

// ==================== API 回傳格式 ====================

/**
 * 提交分析的回傳（POST /webhook/analyze）
 */
export const MOCK_SUBMIT_RESPONSE = {
    success: true,
    session_id: 'mock-session-12345'
};

/**
 * 分析結果的回傳（GET /webhook/result）
 */
export const MOCK_RESULT = {
    status: 'completed',
    data: {
        // ==================== A 區：氣色分析 ====================
        sectionA: {
            photoUrl: 'https://via.placeholder.com/400x400/FFE4E1/333?text=User+Photo',
            score: 78,
            evaluation: '整體氣色不錯，膚色均勻有光澤。眼周稍有疲態，建議加強眼部保養及充足睡眠。T字部位略有出油，可加強控油保濕。',
            massage: {
                name: '提亮按摩法',
                gifUrl: 'https://via.placeholder.com/200x200/E8F5E9/333?text=Massage+GIF',
                description: '用指腹從下巴開始，沿著臉部輪廓向上提拉，每次按摩 3-5 分鐘。',
                effect: '促進血液循環，提亮膚色，緊緻輪廓線條。'
            }
        },

        // ==================== B 區：膚況分析 ====================
        sectionB: {
            maskedPhotoUrl: 'https://via.placeholder.com/400x400/E3F2FD/333?text=Masked+Photo',
            scores: {
                acne: 3.2,        // 痘痘
                comedone: 4.5,   // 粉刺
                darkCircle: 6.8, // 黑眼圈
                spot: 2.1,       // 斑
                wrinkle: 3.5     // 細紋
            },
            topIssues: [
                {
                    id: 'darkCircle',
                    name: '黑眼圈',
                    score: 6.8,
                    description: '眼周肌膚較暗沉，可能與睡眠不足、用眼過度有關。建議使用含有維他命C、咖啡因的眼部產品，並保持充足睡眠。'
                },
                {
                    id: 'comedone',
                    name: '粉刺',
                    score: 4.5,
                    description: 'T字部位有輕微粉刺，與油脂分泌旺盛有關。建議定期深層清潔，使用含有水楊酸的產品幫助代謝角質。'
                }
            ]
        },

        // ==================== C 區：生活建議 ====================
        sectionC: {
            suggestions: [
                {
                    type: 'diet',
                    title: '飲食調整',
                    content: '建議增加富含維他命C的水果（如奇異果、柑橘類），減少油炸及高糖食物攝取。多喝水保持肌膚水潤。'
                },
                {
                    type: 'sleep',
                    title: '睡眠改善',
                    content: '建議每天維持 7-8 小時睡眠，睡前 1 小時避免使用3C產品。可嘗試使用眼罩或耳塞提升睡眠品質。'
                },
                {
                    type: 'exercise',
                    title: '運動建議',
                    content: '每週至少運動 3 次，每次 30 分鐘以上。有氧運動可促進血液循環，幫助肌膚代謝廢物。'
                }
            ]
        },

        // ==================== D 區：產品推薦 ====================
        sectionD: {
            ingredients: [
                {
                    name: '維他命C',
                    description: '抗氧化、提亮膚色、淡化黑眼圈'
                },
                {
                    name: '水楊酸',
                    description: '溫和代謝角質、清除粉刺'
                },
                {
                    name: '玻尿酸',
                    description: '高效保濕、維持肌膚彈性'
                }
            ],
            products: [
                {
                    id: 'prod-001',
                    brand: 'DR.WU',
                    name: '杏仁酸亮白煥膚精華 15%',
                    imageUrl: 'https://via.placeholder.com/200x200/FFF3E0/333?text=DR.WU',
                    ingredients: ['杏仁酸', '玻尿酸'],
                    officialUrl: 'https://www.drwu.com/',
                    momoUrl: 'https://www.momoshop.com.tw/'
                },
                {
                    id: 'prod-002',
                    brand: '理膚寶水',
                    name: '淨透煥膚極效精華',
                    imageUrl: 'https://via.placeholder.com/200x200/E8F5E9/333?text=LRP',
                    ingredients: ['水楊酸', '菸鹼醯胺'],
                    officialUrl: 'https://www.lrp.com.tw/',
                    momoUrl: 'https://www.momoshop.com.tw/'
                },
                {
                    id: 'prod-003',
                    brand: "Kiehl's",
                    name: '激光極淨白淡斑精華',
                    imageUrl: 'https://via.placeholder.com/200x200/E3F2FD/333?text=Kiehls',
                    ingredients: ['維他命C', '透明質酸'],
                    officialUrl: 'https://www.kiehls.com.tw/',
                    momoUrl: 'https://www.momoshop.com.tw/'
                },
                {
                    id: 'prod-004',
                    brand: 'PAULA\'S CHOICE',
                    name: '2%水楊酸精華液',
                    imageUrl: 'https://via.placeholder.com/200x200/FCE4EC/333?text=Paula',
                    ingredients: ['水楊酸', '綠茶萃取'],
                    officialUrl: 'https://www.paulaschoice.com.tw/',
                    momoUrl: 'https://www.momoshop.com.tw/'
                },
                {
                    id: 'prod-005',
                    brand: 'OLAY',
                    name: '高效透白光塑淡斑精華',
                    imageUrl: 'https://via.placeholder.com/200x200/F3E5F5/333?text=OLAY',
                    ingredients: ['菸鹼醯胺', '維他命C'],
                    officialUrl: 'https://www.olay.com.tw/',
                    momoUrl: 'https://www.momoshop.com.tw/'
                },
                {
                    id: 'prod-006',
                    brand: 'CLARINS',
                    name: '極效光透白淡斑精華',
                    imageUrl: 'https://via.placeholder.com/200x200/FFF8E1/333?text=CLARINS',
                    ingredients: ['維他命C', '植物萃取'],
                    officialUrl: 'https://www.clarins.com.tw/',
                    momoUrl: 'https://www.momoshop.com.tw/'
                }
            ]
        }
    }
};

// ==================== 輔助函數 ====================

/**
 * 模擬 API 延遲
 * @param {number} ms - 延遲毫秒數
 */
export function delay(ms = 1000) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 模擬提交分析 API
 * @returns {Promise<Object>}
 */
export async function mockSubmitAnalysis() {
    await delay(500);
    console.log('🔧 [Mock] 模擬提交分析完成');
    return MOCK_SUBMIT_RESPONSE;
}

/**
 * 模擬取得結果 API（含輪詢模擬）
 * @param {Function} onProgress - 進度回調
 * @returns {Promise<Object>}
 */
export async function mockGetResult(onProgress = null) {
    const steps = [
        { progress: 20, text: '上傳照片中...' },
        { progress: 40, text: 'AI 分析膚況...' },
        { progress: 60, text: '生成建議中...' },
        { progress: 80, text: '查詢推薦產品...' },
        { progress: 100, text: '分析完成！' }
    ];

    for (const step of steps) {
        await delay(600);
        if (onProgress) {
            onProgress(step.progress, step.text);
        }
        console.log(`🔧 [Mock] ${step.text} (${step.progress}%)`);
    }

    return { success: true, data: MOCK_RESULT.data };
}
