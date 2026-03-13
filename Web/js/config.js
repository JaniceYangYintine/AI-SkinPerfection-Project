/**
 * 應用程式設定檔
 * 集中管理所有可配置的參數
 */

export const CONFIG = {
    // API 設定
    API: {
        BASE_URL: 'https://kaden-calisthenical-jin.ngrok-free.dev',
        ENDPOINTS: {
            ANALYZE: '/webhook-test/d-section', //回傳
            RESULT: '/webhook/result' //回傳回去給顯示
        },
        TIMEOUT: 30000,        // API 逾時時間（毫秒）
        POLL_INTERVAL: 2000,   // 輪詢間隔（毫秒）
        MAX_RETRIES: 3         // 最大重試次數
    },

    // LIFF 設定
    LIFF: {
        LIFF_ID: '2008970725-IkuHE9OS'
    },

    // 相機設定
    CAMERA: {
        WIDTH: 1280,
        HEIGHT: 720,
        FACING_MODE: 'user',           // 前鏡頭
        IMAGE_QUALITY: 0.85,           // JPEG 品質
        OUTPUT_WIDTH: 960,             // 輸出寬度（4:3 直向）
        OUTPUT_HEIGHT: 1280,           // 輸出高度（4:3 直向）
        MIN_BRIGHTNESS: 50,            // 最低亮度閾值 (0-255) - 已降低以支持較暗環境
        FACE_DETECTION_INTERVAL: 100   // 臉部偵測間隔（毫秒）
    },

    // 問卷設定
    SURVEY: {
        TOTAL_QUESTIONS: 9,
        AUTO_ADVANCE_DELAY: 300  // 自動跳題延遲（毫秒）
    },

    // 結果頁設定
    RESULT: {
        DEFAULT_TAB: 'A',
        TABS: ['A', 'B', 'C', 'D']
    },

    // 雷達圖設定
    RADAR: {
        SIZE: 300,
        DIMENSIONS: ['acne', 'comedone', 'darkCircle', 'spot', 'wrinkle'],
        LABELS: ['痘痘', '粉刺', '黑眼圈', '斑', '細紋'],
        MAX_VALUE: 10,
        COLORS: {
            FILL: 'rgba(205, 169, 110, 0.3)',
            STROKE: 'rgba(205, 169, 110, 1)',
            GRID: 'rgba(0, 0, 0, 0.1)',
            TEXT: '#333333'
        }
    },

    // 儲存鍵名
    STORAGE_KEYS: {
        PHOTO: 'skincare_photo',
        ANSWERS: 'skincare_answers',
        LINE_ID: 'line_id'
    }
};

// 問卷題目定義
export const SURVEY_QUESTIONS = [
    {
        id: 'age',
        title: '您的年齡區間？',
        options: [
            { value: 'under20', label: '20歲以下' },
            { value: '20-30', label: '20-30歲' },
            { value: '30-40', label: '30-40歲' },
            { value: 'over40', label: '40歲以上' }
        ]
    },
    {
        id: 'skinCondition',
        title: '清潔肌膚後30分鐘，膚況是？',
        options: [
            { value: 'dry', label: '全臉乾燥緊繃脫皮' },
            { value: 'oily', label: '全臉出油泛油光' },
            { value: 'combo', label: 'T字出油兩頰乾' },
            { value: 'comfortable', label: '全臉舒適' }
        ]
    },
    {
        id: 'sensitivity',
        title: '您對外界刺激或新產品的敏感程度？',
        options: [
            { value: 'high', label: '容易泛紅敏感' },
            { value: 'medium', label: '偶爾會但可接受' },
            { value: 'low', label: '幾乎沒有問題' }
        ]
    },
    {
        id: 'rhythm',
        title: '您更偏好哪種保養節奏？',
        options: [
            { value: 'complete', label: '早晚完整一套' },
            { value: 'single', label: '僅早或晚單一步驟' },
            { value: 'random', label: '隨性不固定' }
        ]
    },
    {
        id: 'sleepHours',
        title: '最近一週的平均睡眠時數？',
        options: [
            { value: 'less6', label: '少於6小時' },
            { value: '6-7', label: '6-7小時' },
            { value: '7-8', label: '7-8小時' },
            { value: 'over8', label: '超過8小時' }
        ]
    },
    {
        id: 'stress',
        title: '最近覺得壓力大嗎？',
        options: [
            { value: 'none', label: '幾乎沒有' },
            { value: 'sometimes', label: '偶爾覺得有' },
            { value: 'often', label: '經常覺得壓力大' }
        ]
    },
    {
        id: 'exercise',
        title: '一週大約幾天有運動超過30分鐘？',
        options: [
            { value: '0', label: '0天' },
            { value: '1-2', label: '1-2天' },
            { value: '3-4', label: '3-4天' },
            { value: '5-7', label: '5-7天' }
        ]
    },
    {
        id: 'friedFood',
        title: '一週油炸重油食物的頻率？',
        options: [
            { value: '0-1', label: '0-1次' },
            { value: '2-3', label: '2-3次' },
            { value: '4-5', label: '4-5次' },
            { value: '6over', label: '6次以上' }
        ]
    },
    {
        id: 'diet',
        title: '您每天蔬果攝取量？',
        options: [
            { value: 'balanced', label: '很多均衡' },
            { value: 'low', label: '一般少量' },
            { value: 'none', label: '很少幾乎沒有' }
        ]
    }
];

// 錯誤訊息定義
export const ERROR_MESSAGES = {
    CAMERA_PERMISSION_DENIED: '請允許相機權限才能繼續使用',
    CAMERA_NOT_SUPPORTED: '您的瀏覽器不支援相機功能，請使用 Chrome 或 Safari',
    API_TIMEOUT: '分析逾時，請重試',
    API_ERROR: '分析失敗，請稍後重試',
    NETWORK_ERROR: '網路連線異常，請檢查網路後重試',
    FACE_NOT_DETECTED: '未偵測到臉部，請將臉對準框線',
    BRIGHTNESS_LOW: '光線不足，請移至光線充足處'
};

// 提示訊息定義
export const TIPS = {
    FACE_TOO_FAR: '請靠近一點',
    FACE_TOO_CLOSE: '請稍微後退',
    FACE_LEFT: '請往右移動',
    FACE_RIGHT: '請往左移動',
    FACE_UP: '請往下移動',
    FACE_DOWN: '請往上移動',
    PERFECT: '完美！請保持不動',
    READY: '可以拍照了'
};
