# A 區行動推薦系統 - 整合說明

## 📋 系統概述

這個系統會根據 LLM 偵測到的肌膚問題，自動顯示對應的行動建議和教學媒體。

---

## 📁 檔案結構

```
project_new/
├── data/
│   └── action-recommendations.json    # 行動推薦資料檔
├── js/
│   └── action-recommendations.js      # 行動推薦管理模組
├── assets/
│   └── action-recommendations.css     # 樣式檔案
├── media/
│   ├── 1.mp4                          # 面部明暗分布教學影片
│   ├── 2.mp4                          # 面部紋理滑度教學影片
│   ├── 3.mp4                          # 神經肌肉張力教學影片
│   ├── ...                            # 其他教學媒體（4-10）
│   └── README.md                      # 媒體檔案說明
└── action-recommendations-demo.html   # 使用範例頁面
```

---

## 🎯 整合步驟

### 步驟 1：引入必要檔案

在你的 `result_new.html` 中加入以下程式碼：

```html
<head>
  <!-- 其他 head 內容 -->
  <link rel="stylesheet" href="/assets/action-recommendations.css">
</head>

<body>
  <!-- 其他 body 內容 -->
  
  <!-- A 區容器 -->
  <div id="section-a-container"></div>
  
  <!-- 引入 JavaScript -->
  <script src="/js/action-recommendations.js"></script>
</body>
```

### 步驟 2：初始化系統

在你的頁面載入時初始化管理器：

```javascript
// 初始化行動推薦管理器
async function initPage() {
  await actionRecommendationManager.init();
  console.log('✅ 行動推薦系統已就緒');
}

window.addEventListener('DOMContentLoaded', initPage);
```

### 步驟 3：接收 LLM 結果並顯示

當你從後端接收到 LLM 分析結果後：

```javascript
// 假設 LLM 回傳的資料格式
const llmResponse = {
  summary: "您的肌膚整體狀況良好，但在以下幾個方面有改善空間...",
  detectedIssues: [1, 3, 5, 7]  // 偵測到的問題 ID
};

// 顯示行動推薦
actionRecommendationManager.displayRecommendations(
  llmResponse.detectedIssues,     // 問題 ID 陣列
  '#section-a-container',          // 容器選擇器
  llmResponse.summary              // 總評文字（可選）
);
```

---

## 🔧 API 使用說明

### `actionRecommendationManager.init()`
初始化管理器，載入資料檔案。

**回傳值**：`Promise<boolean>`

```javascript
const success = await actionRecommendationManager.init();
if (success) {
  console.log('初始化成功');
}
```

### `actionRecommendationManager.displayRecommendations(detectedIssues, containerSelector, summary)`
顯示行動推薦。

**參數**：
- `detectedIssues` (Array<number>)：偵測到的問題 ID 陣列，例如 `[1, 3, 5]`
- `containerSelector` (string)：要顯示內容的容器選擇器，例如 `'#section-a-container'`
- `summary` (string, 可選)：LLM 生成的總評文字

**範例**：
```javascript
actionRecommendationManager.displayRecommendations(
  [1, 2, 3],
  '#section-a-container',
  '您的肌膚狀況良好...'
);
```

### `actionRecommendationManager.getAction(actionId)`
取得單個行動資料。

**參數**：
- `actionId` (number)：行動 ID (1-10)

**回傳值**：`Object | null`

```javascript
const action = actionRecommendationManager.getAction(1);
console.log(action.targetIssue);  // "面部明暗分布"
```

### `actionRecommendationManager.getAllActions()`
取得所有行動資料。

**回傳值**：`Object | null`

```javascript
const allActions = actionRecommendationManager.getAllActions();
```

---

## 📊 資料格式說明

### LLM 回傳格式（建議）

```json
{
  "summary": "LLM 生成的總評文字",
  "detectedIssues": [1, 3, 5, 7],
  "confidence": {
    "1": 0.85,
    "3": 0.72,
    "5": 0.68,
    "7": 0.91
  }
}
```

### 問題 ID 對照表

| ID | 問題類型 | 媒體檔案 |
|----|---------|---------|
| 1  | 面部明暗分布 | media/1.mp4 |
| 2  | 面部紋理滑度 | media/2.mp4 |
| 3  | 神經肌肉張力 | media/3.mp4 |
| 4  | 眼神聚焦感 | media/4.mp4 |
| 5  | 組織水分感 | media/5.mp4 |
| 6  | 面部輪廓線 | media/6.mp4 |
| 7  | 眉位緊縮度 | media/7.mp4 |
| 8  | 異質彈吸感 | media/8.mp4 |
| 9  | 頸前線條 | media/9.mp4 |
| 10 | 眼神透亮度 | media/10.mp4 |

---

## 🎨 自訂樣式

如果你想調整樣式，可以覆寫 CSS 變數或直接修改 `action-recommendations.css`。

**範例**：調整卡片顏色
```css
.action-card {
  background: #f0f0f0;  /* 自訂背景色 */
}

.card-header {
  background: linear-gradient(135deg, #your-color-1, #your-color-2);
}
```

---

## 🧪 測試

1. 開啟 `action-recommendations-demo.html` 查看範例
2. 點擊不同的測試按鈕，查看不同偵測結果的顯示效果
3. 確認媒體檔案能正確載入

---

## 📦 待辦事項

- [ ] 將你的教學影片/圖片放入 `media/` 資料夾
  - 檔案命名：`1.mp4`, `2.mp4`, ..., `10.mp4`（或 `.png`）
- [ ] 整合到 `result_new.html` 的 A 區
- [ ] 連接後端 LLM API
- [ ] 測試完整流程

---

## ❓ 常見問題

### Q1: 媒體檔案可以混用 MP4 和 PNG 嗎？
A: 可以！系統會根據 `action-recommendations.json` 中的 `mediaType` 和 `mediaUrl` 自動判斷。

### Q2: 如何修改媒體檔案路徑？
A: 編輯 `data/action-recommendations.json`，修改對應的 `mediaUrl` 欄位。

### Q3: 可以同時顯示多個問題嗎？
A: 可以！只要在 `detectedIssues` 陣列中傳入多個 ID 即可。

### Q4: 如何新增第 11 個問題類型？
A: 
1. 在 `action-recommendations.json` 中新增 `"11": {...}` 資料
2. 將對應的媒體檔案放入 `media/11.mp4`

---

## 📞 需要協助？

如有任何問題，請檢查瀏覽器 Console 的錯誤訊息，或參考 `action-recommendations-demo.html` 的範例程式碼。
