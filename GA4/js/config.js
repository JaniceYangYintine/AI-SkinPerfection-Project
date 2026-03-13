/**
 * 應用程式設定檔
 * ======================================================
 * 集中管理所有可配置的參數、常數、magic numbers
 * 更新：2026-02-01
 */

export const CONFIG = {
    // ==================== API 設定 ====================
    API: {
        BASE_URL: 'https://lumpier-odessa-distinguishingly.ngrok-free.dev',
        ENDPOINTS: {
            ANALYZE: '/webhook/analyze',
            RESULT: '/webhook/result'
        },
        TIMEOUT: 30000,
        POLL_INTERVAL: 2000,
        MAX_RETRIES: 3,
        MAX_POLL_ATTEMPTS: 60  // 最大輪詢次數 (60 * 2秒 = 120秒)
    },

    // ==================== LIFF 設定 ====================
    LIFF: {
        LIFF_ID: '2008825433-EiKVRQPf'
    },

    // ==================== 相機設定 ====================
    CAMERA: {
        // 相機解析度
        WIDTH: 1280,
        HEIGHT: 720,
        FACING_MODE: 'user',

        // 輸出設定
        IMAGE_QUALITY: 0.85,
        OUTPUT_WIDTH: 960,
        OUTPUT_HEIGHT: 1280,

        // 偵測參數
        MIN_BRIGHTNESS: 50,
        FACE_DETECTION_INTERVAL: 100,

        // 臉部偵測容差
        FACE_DETECTION: {
            IDEAL_X: 0.5,           // 理想 X 位置 (中心)
            IDEAL_Y: 0.45,          // 理想 Y 位置 (稍微偏上)
            IDEAL_SIZE: 0.25,       // 理想臉部大小 (螢幕比例)
            TOLERANCE_POSITION: 0.25, // 位置容差（允許較多偏移）
            TOLERANCE_SIZE: 0.15,     // 大小容差
            MIN_SIZE: 0.10,         // 最小臉部大小
            MAX_SIZE: 0.50          // 最大臉部大小
        },

        // 亮度偵測參數
        BRIGHTNESS: {
            SAMPLE_SIZE: 100,       // 取樣尺寸
            // RGB 轉灰階係數 (ITU-R BT.601)
            COEFFICIENTS: {
                R: 0.299,
                G: 0.587,
                B: 0.114
            }
        }
    },

    // ==================== 問卷設定 ====================
    SURVEY: {
        TOTAL_QUESTIONS: 9,
        AUTO_ADVANCE_DELAY: 300
    },

    // ==================== 結果頁設定 ====================
    RESULT: {
        // 預設顯示模式：'summary'（總覽）或 'detail'（詳情 Tab）
        DEFAULT_VIEW: 'summary',
        DEFAULT_TAB: 'A',
        TABS: ['A', 'B', 'C', 'D'],
        TAB_LABELS: {
            'A': 'A 活力氣色指南',
            'B': 'B 智能膚況解析',
            'C': 'C 由內而外養膚',
            'D': 'D 智慧配方'
        },
        // 總覽頁卡片標題
        SUMMARY_TITLES: {
            'A': '活力氣色指南',
            'B': '智能膚況解析',
            'C': '由內而外養膚',
            'D': '智慧配方'
        },
        // 返回頂部按鈕顯示閾值
        BACK_TO_TOP_THRESHOLD: 300
    },

    // ==================== 雷達圖設定 ====================
    RADAR: {
        SIZE: 300,
        RADIUS_RATIO: 0.35,         // 半徑佔畫布比例
        GRID_LEVELS: 5,             // 網格層數
        LABEL_OFFSET: 25,           // 標籤偏移距離
        ANIMATION_DURATION: 1000,   // 動畫時間 (ms)
        DIMENSIONS: ['acne', 'comedone', 'darkCircle', 'spot', 'wrinkle'],
        LABELS: ['痘痘', '粉刺', '黑眼圈', '斑', '細紋'],
        MAX_VALUE: 5,
        COLORS: {
            FILL: 'rgba(205, 169, 110, 0.3)',
            STROKE: 'rgba(205, 169, 110, 1)',
            GRID: 'rgba(0, 0, 0, 0.1)',
            TEXT: '#333333'
        }
    },

    // ==================== UI 設定 ====================
    UI: {
        // 輪播設定
        CAROUSEL: {
            GAP: 16,                // 項目間距
            SCROLL_DEBOUNCE: 100    // 滾動事件防抖
        },
        // 圓形進度環
        CIRCULAR_PROGRESS: {
            VIEWBOX_SIZE: 160,
            CENTER: 80,
            RADIUS: 70,
            STROKE_WIDTH: 12,
            CIRCUMFERENCE: 440      // 2 * PI * 70 ≈ 440
        },
        // 動畫時間
        ANIMATION: {
            FAST: 150,
            BASE: 200,
            SLOW: 300,
            PROGRESS: 1500
        },
        // Toast 提示
        TOAST: {
            DURATION: 3000
        }
    },

    // ==================== 外部連結 ====================
    EXTERNAL_URLS: {
        MOMO_SEARCH: 'https://www.momoshop.com.tw/search/searchShop.jsp?keyword='
    },

    // ==================== 儲存鍵名 ====================
    STORAGE_KEYS: {
        PHOTO: 'skincare_photo',
        ANSWERS: 'skincare_answers',
        LINE_ID: 'line_id'
    }
};

// ==================== SVG 圖示路徑 ====================
export const ICON_PATHS = {
    food: 'assets/icons/food.svg',
    diet: 'assets/icons/diet.svg',
    sleep: 'assets/icons/sleep.svg',
    exercise: 'assets/icons/exercise.svg',
    stress: 'assets/icons/stress.svg',
    skincare: 'assets/icons/skincare.svg',
    lightbulb: 'assets/icons/lightbulb.svg',
    warning: 'assets/icons/warning.svg'
};

// ==================== 圖示無障礙標籤 ====================
export const ICON_LABELS = {
    food: '食物',
    diet: '飲食',
    sleep: '睡眠',
    exercise: '運動',
    stress: '舒壓',
    skincare: '護膚',
    lightbulb: '提示',
    warning: '警告'
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
