/**
 * 行動推薦系統整合腳本
 * 將這段程式碼加入到 result_new.html 的 </body> 前
 */

// 引入行動推薦系統
const actionRecommendationScript = document.createElement('script');
actionRecommendationScript.src = '/js/action-recommendations.js';
document.body.appendChild(actionRecommendationScript);

// 等待載入完成後初始化
actionRecommendationScript.onload = async function () {
    try {
        // 初始化管理器
        await actionRecommendationManager.init();
        console.log('✅ 行動推薦系統已初始化');

        // 從 localStorage 或 API 取得 LLM 偵測結果
        const result = loadResult ? loadResult() : null;

        // 🎯 假資料在這裡！
        // 模擬 LLM 偵測結果（實際應從後端 API 取得）
        const llmDetection = result?.llm_detection || {
            summary: "您的肌膚整體狀況良好，但在以下幾個方面有改善空間。透過簡單的動作調整，可以快速提升氣色表現。",
            detectedIssues: [1, 4, 5, 10]  // 👈 這裡就是假資料！改這個陣列可以測試不同組合
        };

        // 顯示行動推薦
        if (llmDetection.detectedIssues && llmDetection.detectedIssues.length > 0) {
            actionRecommendationManager.displayRecommendations(
                llmDetection.detectedIssues,
                '#action-recommendations-container',
                llmDetection.summary
            );
            console.log('✅ 行動推薦已顯示');
        }
    } catch (error) {
        console.error('❌ 行動推薦系統初始化失敗:', error);
    }
};
