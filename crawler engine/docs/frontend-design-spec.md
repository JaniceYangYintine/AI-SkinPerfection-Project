# 膚況分析系統 - 前端設計文件

## 📋 目錄
1. [系統架構](#系統架構)
2. [頁面流程](#頁面流程)
3. [資料格式定義](#資料格式定義)
4. [API 整合規格](#api-整合規格)
5. [開發模式說明](#開發模式說明)
6. [部署檢查清單](#部署檢查清單)

---

## 🏗️ 系統架構

### 技術棧
- **前端框架**: 純 HTML/CSS/JavaScript (ES6 Modules)
- **樣式系統**: 星巴克風格設計系統
- **API 整合**: n8n Webhook
- **資料儲存**: localStorage + Session Storage
- **部署平台**: GitHub Pages

### 檔案結構
```
project_new/
├── index.html              # 首頁
├── camera_new.html         # 拍照頁
├── survey_new.html         # 問卷頁
├── result_new.html         # 結果頁
├── css/
│   ├── app.css            # 主要樣式
│   └── design-system.css  # 設計系統
├── js/
│   ├── api-config.js      # API 設定
│   ├── utils.js           # 工具函數 (含 API 呼叫)
│   └── result/
│       ├── main.js        # 結果頁主程式
│       ├── section-a.js   # A區: 氣色分析
│       ├── section-b.js   # B區: 膚況分析
│       ├── section-c.js   # C區: 生活建議
│       └── section-d.js   # D區: 產品推薦
└── api/
    └── mock_result.json   # Mock 測試資料
```

---

## 🔄 頁面流程

### 使用者旅程
```
1. 首頁 (index.html)
   ↓ 點擊「開始分析」
   
2. 拍照頁 (camera_new.html)
   ↓ 拍攝照片 (MediaPipe 品質檢測)
   ↓ 照片儲存到 localStorage.user_photo (Base64)
   
3. 問卷頁 (survey_new.html)
   ↓ 填寫 9 題問卷
   ↓ 提交分析 (呼叫 submitAnalysis())
   ↓ 取得 session_id
   
4. 結果頁 (result_new.html)
   ↓ 輪詢結果 (呼叫 pollAnalysisResult())
   ↓ 顯示 A/B/C/D 四區結果
```

### 資料流
```
前端 → n8n Webhook → AI 分析 → 資料庫 → 前端輪詢 → 顯示結果
```

---

## 📊 資料格式定義

### 1. 提交分析 (POST /webhook/analyze)

**Request (FormData)**:
```javascript
{
  photo: Blob,              // 照片檔案
  line_user_id: "U123...",  // LINE User ID
  answers: JSON.stringify({ // 問卷答案
    q1: "20-30歲",
    q2: "混合性",
    q3: "經常熬夜",
    // ... 共 9 題
  })
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "uuid-1234-5678",
  "message": "分析中..."
}
```

---

### 2. 取得結果 (GET /webhook/result?session_id=xxx)

**Response 完整格式**:
```json
{
  "session_id": "uuid-1234-5678",
  "status": "completed",
  "timestamp": "2026-01-26T10:00:00Z",
  
  // 使用者照片
  "photo_url": "https://storage.googleapis.com/...",
  
  // A區: 氣色分析
  "a_score": 84,
  "a_summary": "您的氣色整體良好...",
  "a_issue": "眼睛疲勞",
  "a_issue_detail": "靜脈瘀血",
  "a_actions": [
    {
      "name": "眼部冷熱交替",
      "desc": "冷熱敷交替,改善眼周暗沈",
      "effect": "減少眼周暗沉與疲憊感",
      "gif": ""
    }
  ],
  "ai_diagnosis": {
    "positive_feedback": "您的氣色整體穩定...",
    "problem_analysis": "眼周區域略顯疲態..."
  },
  
  // B區: 膚況分析 (1-5 分制)
  "b_scores": {
    "darkCircles": 3.9,
    "acne": 3.1,
    "comedones": 2.7,
    "wrinkles": 2.1,
    "spots": 3.5
  },
  "b_top_issues": [
    {
      "name": "黑眼圈",
      "key": "darkCircles",
      "score": 3.9,
      "llm_analysis": "眼周區域循環不佳..."
    }
  ],
  "mask_url": "https://storage.googleapis.com/.../mask.jpg",
  
  // C區: 生活建議
  "lifestyle_advice": {
    "nutrition": {
      "summary": "增加蔬果、減少油炸",
      "detail": "建議每天攝取 5 份蔬果...",
      "items": [
        "深綠色蔬菜 (菠菜、羽衣甘藍)",
        "Omega-3 食物 (鮭魚、核桃)"
      ]
    },
    "sleep": {
      "summary": "每晚 7-8 小時睡眠",
      "detail": "建議固定就寢時間..."
    },
    "exercise": {
      "summary": "每週至少 3 次運動",
      "detail": "保持規律運動..."
    }
  },
  
  // D區: 產品推薦
  "d_product_recommendations": {
    "ingredients": [
      {
        "issue_name": "黑眼圈",
        "primary_ingredient": "咖啡因",
        "core_ingredients": ["維生素K", "煙醯胺"],
        "description": "咖啡因能促進眼周血液循環..."
      }
    ],
    "products": [
      {
        "id": 1,
        "name": "Dr.Wu 杏仁酸亮白煥膚精華",
        "brand": "Dr.Wu",
        "image_url": "https://...",
        "product_url": "https://www.drwu.com/",
        "momo_url": "https://www.momoshop.com.tw/search/searchShop.jsp?keyword=Dr.Wu+杏仁酸",
        "ingredients": ["杏仁酸", "煙醯胺", "維生素C"]
      }
    ]
  }
}
```

---

## 🔌 API 整合規格

### 設定檔: `js/api-config.js`

```javascript
export const API_CONFIG = {
    // n8n Webhook URL (請替換為實際 URL)
    N8N_ANALYZE_URL: 'https://your-n8n.app.n8n.cloud/webhook/analyze',
    N8N_RESULT_URL: 'https://your-n8n.app.n8n.cloud/webhook/result',
    
    // 超時設定
    TIMEOUT: 30000,        // 30 秒
    POLL_INTERVAL: 2000,   // 每 2 秒輪詢一次
    
    // 開發模式 (true: 使用 mock 資料, false: 呼叫實際 API)
    DEV_MODE: true
};
```

### API 呼叫函數: `js/utils.js`

#### 1. 提交分析
```javascript
import { submitAnalysis, getLineUserId } from './js/utils.js';

const result = await submitAnalysis({
    photoBase64: localStorage.getItem('user_photo'),
    answers: { q1: "...", q2: "..." },
    lineUserId: getLineUserId()
});

if (result.success) {
    console.log('Session ID:', result.session_id);
}
```

#### 2. 輪詢結果
```javascript
import { pollAnalysisResult } from './js/utils.js';

pollAnalysisResult({
    sessionId: 'uuid-1234',
    timeout: 30000,
    interval: 2000,
    onProgress: ({ elapsed, timeout, status }) => {
        console.log(`進度: ${elapsed}ms / ${timeout}ms`);
    },
    onComplete: (result) => {
        console.log('分析完成:', result);
    },
    onError: (message) => {
        console.error('錯誤:', message);
    }
});
```

---

## 🛠️ 開發模式說明

### 開發模式 (DEV_MODE: true)
- ✅ 不呼叫實際 API
- ✅ 使用 `api/mock_result.json` 假資料
- ✅ 模擬 1-2 秒延遲
- ✅ 適合前端開發和測試

### 正式模式 (DEV_MODE: false)
- ✅ 呼叫實際 n8n Webhook
- ✅ 真實的照片上傳和分析
- ✅ 輪詢等待結果
- ✅ 錯誤處理和降級方案

### 切換方式
修改 `js/api-config.js`:
```javascript
DEV_MODE: false  // 改為 false 即可
```

---

## 📋 部署檢查清單

### 上線前必須完成:

#### 1. API 設定
- [ ] 填入實際的 `N8N_ANALYZE_URL`
- [ ] 填入實際的 `N8N_RESULT_URL`
- [ ] 將 `DEV_MODE` 改為 `false`
- [ ] 確認 CORS 設定正確

#### 2. LIFF 設定
- [ ] 填入實際的 `LIFF_ID` (在 `api-config.js`)
- [ ] 測試 LINE 登入流程
- [ ] 確認可以取得 LINE User ID

#### 3. GA4 追蹤
- [ ] 填入 `MEASUREMENT_ID` (在 `api-config.js`)
- [ ] 測試事件追蹤 (產品點擊等)

#### 4. 資料格式驗證
- [ ] 確認後端回傳的 JSON 格式與 `mock_result.json` 一致
- [ ] 測試所有欄位都有正確顯示
- [ ] 確認 momo_url 格式正確

#### 5. 錯誤處理
- [ ] 測試網路錯誤情境
- [ ] 測試 API 超時情境
- [ ] 確認降級方案 (使用 localStorage)

#### 6. 效能優化
- [ ] 壓縮照片大小 (建議 < 2MB)
- [ ] 測試輪詢間隔是否合理
- [ ] 確認 Loading 動畫顯示

---

## 🎨 設計規格

### 評分系統

#### A區 (氣色分析)
- 分數範圍: 0-100 分
- 顯示: 圓形進度圈

#### B區 (膚況分析)
- 分數範圍: **1-5 分** (已更新)
- 嚴重度分級:
  - 1.0-1.9: 輕微 (綠色)
  - 2.0-3.4: 中等 (橘色)
  - 3.5-5.0: 嚴重 (紅色)

### 手機版優化
- ✅ 卡片填滿寬度 (無左右留白)
- ✅ 產品連結垂直排列
- ✅ 響應式設計

### 產品卡片
- ✅ 顯示品牌、名稱、成分
- ✅ 兩個連結: 官網 + momo
- ✅ 移除價格顯示

---

## 📞 後端協作事項

### 需要後端提供:

1. **n8n Webhook URL**
   - 提交分析: `/webhook/analyze`
   - 取得結果: `/webhook/result`

2. **回傳資料格式**
   - 必須符合本文件的 JSON 格式
   - 特別注意 B區評分為 1-5 分

3. **momo_url 生成邏輯**
   - 建議在 n8n 中動態生成
   - 格式: `https://www.momoshop.com.tw/search/searchShop.jsp?keyword={品牌}+{產品關鍵字}`

4. **CORS 設定**
   - 允許前端網域存取
   - 允許 POST 和 GET 方法

---

## 🔍 測試指南

### 開發環境測試
```bash
# 1. 啟動本地伺服器
python -m http.server 8000

# 2. 開啟瀏覽器
http://localhost:8000/index.html

# 3. 完整流程測試
拍照 → 問卷 → 查看結果 (使用 mock 資料)
```

### 正式環境測試
1. 將 `DEV_MODE` 改為 `false`
2. 填入實際 n8n URL
3. 測試完整流程
4. 檢查 Console 是否有錯誤

---

## 📝 版本記錄

### v1.0 (2026-01-26)
- ✅ 完成 A/B/C/D 四區設計
- ✅ 整合 n8n API
- ✅ B區評分改為 1-5 分
- ✅ 手機版優化
- ✅ 產品推薦加入 momo 連結

---

## 🆘 常見問題

### Q: 為什麼結果頁顯示不出資料?
A: 檢查以下項目:
1. Console 是否有錯誤訊息
2. `session_id` 是否存在於 localStorage
3. `DEV_MODE` 設定是否正確
4. Mock 資料檔案是否存在

### Q: 如何測試 n8n API?
A: 使用 Postman 或 curl:
```bash
curl -X POST https://your-n8n-url/webhook/analyze \
  -F "photo=@test.jpg" \
  -F "line_user_id=test123" \
  -F "answers={\"q1\":\"20-30歲\"}"
```

### Q: momo 連結沒有顯示?
A: 確認:
1. `mock_result.json` 中有 `momo_url` 欄位
2. JavaScript 沒有錯誤
3. CSS 沒有隱藏連結

---

**文件版本**: 1.0  
**最後更新**: 2026-01-26  
**維護者**: Chelsea
