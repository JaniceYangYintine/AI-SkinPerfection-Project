/**
 * 應用程式設定檔
 * 集中管理所有設定參數，方便維護與調整
 */
export const CONFIG = {
    // LINE LIFF 設定
    LIFF_ID: '2008825433-EiKVRQPf', // 注意：你原本 main 裡用的是 2008825433-EiKVRQPf，請確認哪一個才是正確的

    // API 設定
    API_URL: 'https://lumpier-odessa-distinguishingly.ngrok-free.dev/webhook-test/skin-analysis',

    // 效能設定
    FPS_LIMIT: 30, // 限制在 30 FPS 以節省電力

    // 對齊檢測閾值
    ALIGNMENT_THRESHOLDS: {
        PERFECT: { dist: 30, ratioMin: 0.85, ratioMax: 1.0 },
        GOOD: { dist: 45, ratioMin: 0.65, ratioMax: 1.15 }
    },

    // 開發模式設定
    SKIP_UPLOAD: false, // 改為 false 才能執行 fetch

    // 框線座標
    GUIDE: {
        cx: 180,
        cy: 228,
        w: 272,
        h: 308
    }
};

/**
 * 主程式邏輯
 */
async function main() {
    try {
        // 1. 初始化 LIFF
        await liff.init({ liffId: CONFIG.LIFF_ID });

        // 2. 檢查登入狀態
        if (!liff.isLoggedIn()) {
            liff.login();
            return; // 導向登入頁，中斷後續執行
        }

        // 3. 取得用戶資料
        const profile = await liff.getProfile();
        
        // 4. 若非開發跳過模式，則上傳資料
        if (!CONFIG.SKIP_UPLOAD) {
            await uploadUserData(profile);
        }

    } catch (error) {
        console.error("LIFF 初始化或執行失敗:", error);
    }
}

/**
 * 封裝上傳邏輯
 */
async function uploadUserData(profile) {
    try {
        const response = await fetch(CONFIG.API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                userId: profile.userId,
                displayName: profile.displayName,
                timestamp: new Date().toISOString() // 額外增加時間戳記建議
            })
        });

        if (response.ok) {
            console.log("資料已成功傳送至後端");
        } else {
            console.error("傳送失敗，狀態碼:", response.status);
        }
    } catch (err) {
        console.error("網路請求出錯:", err);
    }
}

// 啟動程式
main();
