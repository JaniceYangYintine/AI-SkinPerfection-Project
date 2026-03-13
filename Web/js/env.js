/**
 * 環境設定檔
 * 控制開發模式與正式模式的切換
 */

// 自動偵測是否為本地開發環境
export const IS_DEV = location.hostname === 'localhost' || location.hostname === '127.0.0.1';

// 開發用假 User ID（本地測試時使用）
export const DEV_USER_ID = 'dev-user-12345';
