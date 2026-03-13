/**
 * LIFF 初始化與 LINE 資料暫存
 */

import { CONFIG } from '../config.js';
// import { IS_DEV, DEV_USER_ID } from '../env.js';

/**
 * 初始化 LIFF 並暫存 LINE ID
 * @returns {Promise<{success: boolean, profile?: Object, error?: string}>}
 */
export async function initLiff() {
    // 開發模式：跳過 LIFF，使用假 User ID
    // if (IS_DEV) {
    //     console.log('🔧 開發模式：跳過 LIFF 初始化');
    //     sessionStorage.setItem(CONFIG.STORAGE_KEYS.LINE_ID, DEV_USER_ID);
    //     return { success: true, profile: { userId: DEV_USER_ID } };
    // }

    // 正式環境：初始化 LIFF
    if (typeof liff === 'undefined') {
        console.warn('LIFF SDK 未載入，跳過 LIFF 初始化');
        return { success: false, error: 'liff_not_loaded' };
    }

    try {
        await liff.init({ liffId: CONFIG.LIFF.LIFF_ID });

        if (!liff.isLoggedIn()) {
            liff.login();
            return { success: false, error: 'liff_login_required' };
        }

        const profile = await liff.getProfile();
        if (profile && profile.userId) {
            sessionStorage.setItem(CONFIG.STORAGE_KEYS.LINE_ID, profile.userId);
        }

        return { success: true, profile };
    } catch (error) {
        console.warn('LIFF init failed:', error);
        return { success: false, error: 'liff_init_failed' };
    }
}
