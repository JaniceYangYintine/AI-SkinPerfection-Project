# 前端模組化架構筆記

> 更新日期: 2026-01-25

---

## �️ Base64 vs URL

| 項目 | Base64 | URL |
|------|--------|-----|
| 範例 | `data:image/jpeg;base64,/9j/4AA...` | `https://storage.googleapis.com/photo.jpg` |
| 儲存 | 嵌入程式碼 (localStorage) | 遠端伺服器 (GCS) |
| 大小 | 比原圖大 33% | 原圖大小 |
| 用途 | 開發/小圖/離線 | 正式環境/大圖 |

---

## �📖 為什麼要模組化?

### 重構前 (單一檔案)

```
result_new.html (2200+ 行)
├─ HTML 結構 (~500 行)
├─ CSS 樣式 (~600 行)
└─ JavaScript 邏輯 (~1100 行)
    ├─ 資料載入函數
    ├─ A 區渲染函數
    ├─ B 區渲染函數 + 雷達圖
    ├─ C 區渲染函數
    ├─ D 區渲染函數 + 產品卡片
    └─ 頁面切換函數
```

**問題:**
- ❌ 難以維護 - 修改一個功能要在 2000 行中找
- ❌ 難以測試 - 無法單獨測試某個模組
- ❌ 難以重用 - 雷達圖邏輯無法在其他頁面使用
- ❌ 團隊協作困難 - 多人同時修改容易衝突

---

### 重構後 (模組化)

```
project_new/
├─ result_new.html (HTML + CSS)
├─ vite.config.js (打包配置)
├─ package.json (專案設定)
│
├─ js/result/
│   ├─ main.js          (主入口,協調所有模組)
│   ├─ data-loader.js   (資料載入邏輯)
│   ├─ section-a.js     (A 區:氣色分析)
│   ├─ section-b.js     (B 區:膚況分析)
│   ├─ section-c.js     (C 區:生活建議)
│   └─ section-d.js     (D 區:產品推薦) ⭐
│
└─ js/components/
    └─ radar-chart.js   (雷達圖元件,可重用)
```

**優點:**
- ✅ **關注點分離** - 每個檔案只負責一件事
- ✅ **易於維護** - 修改 D 區只需改 `section-d.js`
- ✅ **易於測試** - 可單獨測試每個模組
- ✅ **可重用** - 雷達圖可以在其他頁面使用
- ✅ **團隊友善** - 不同人改不同檔案

---

## 🔧 關鍵技術

### 1. ES6 Modules

```javascript
// 匯出 (section-d.js)
export function loadSectionD(result) { ... }
export function renderProducts(products) { ... }

// 匯入 (main.js)
import { loadSectionD } from './section-d.js';
```

### 2. Vite 打包工具

| 指令 | 用途 |
|------|------|
| `npm run dev` | 開發模式 (熱更新) |
| `npm run build` | 正式打包 (壓縮) |
| `npm run preview` | 預覽打包結果 |

**開發時:** 多個小檔案,易於除錯
**正式環境:** 打包成單一檔案,效能最佳

### 3. 全域函數暴露

HTML 中的 `onclick` 需要全域函數:

```javascript
// main.js
window.showDetail = showDetail;
window.backToOverview = backToOverview;
window.trackProductClick = trackProductClick;
```

---

## 📁 各模組職責

### `main.js` - 主入口

```javascript
// 協調所有模組
async function init() {
    const result = await loadResultData();
    loadSectionA(result);
    loadSectionB(result);
    loadSectionC(result);
    loadSectionD(result);
}
```

### `data-loader.js` - 資料載入

```javascript
// 從 API 或 localStorage 載入資料
export async function loadResultData() { ... }
export function loadFromLocalStorage() { ... }
```

### `section-d.js` - 產品推薦 ⭐

```javascript
// D 區完整邏輯
export function loadSectionD(result) { ... }
export function renderIngredientsOverview(ingredients) { ... }
export function renderIngredients(ingredients) { ... }
export function renderProducts(products) { ... }
export function trackProductClick(productId) { ... }
```

### `radar-chart.js` - 雷達圖元件

```javascript
// 可重用的雷達圖繪製函數
export function drawRadarChart(canvasId, scores, size) { ... }
```

---

## 🔄 資料流程

```
1. 頁面載入
   ↓
2. main.js 執行 init()
   ↓
3. data-loader.js 從 API 取得資料
   ↓
4. 各區塊模組接收資料並渲染
   ├─ section-a.js → A 區
   ├─ section-b.js → B 區 (使用 radar-chart.js)
   ├─ section-c.js → C 區
   └─ section-d.js → D 區
   ↓
5. 使用者互動
   ├─ showDetail() → 顯示詳情
   ├─ backToOverview() → 返回總覽
   └─ trackProductClick() → 追蹤點擊
```

---

## 📊 效能比較

| 項目 | 單一檔案 | 模組化 (開發) | 模組化 (打包) |
|------|---------|--------------|--------------|
| HTTP 請求數 | 1 | 8+ | 2-3 |
| 檔案大小 | 80KB | 80KB (分散) | 30KB (壓縮) |
| 載入速度 | 中等 | 稍慢 | 最快 ✅ |
| 開發體驗 | 差 | 最佳 ✅ | - |

---

## 🛠️ 日常開發流程

### 1. 啟動開發環境
```bash
cd project_new
npm run dev
```

### 2. 修改程式碼
- 修改 D 區 → 編輯 `js/result/section-d.js`
- 修改雷達圖 → 編輯 `js/components/radar-chart.js`
- 修改資料載入 → 編輯 `js/result/data-loader.js`

### 3. 即時預覽
Vite 會自動熱更新,不需要重新整理頁面

### 4. 正式部署
```bash
npm run build
# 產出 dist/ 目錄,上傳到伺服器
```

---

## 📝 重點回顧

1. **模組化** = 把大檔案拆成小檔案,每個檔案負責一件事
2. **ES6 Modules** = `import`/`export` 語法
3. **Vite** = 現代化的打包工具,開發快速、打包高效
4. **開發時用多檔案,正式環境用打包** = 兩全其美

---

## 🔗 相關檔案

- [vite.config.js](file:///c:/Users/TMP-214/Desktop/cji102_project/project_new/vite.config.js) - Vite 配置
- [main.js](file:///c:/Users/TMP-214/Desktop/cji102_project/project_new/js/result/main.js) - 主入口
- [section-d.js](file:///c:/Users/TMP-214/Desktop/cji102_project/project_new/js/result/section-d.js) - D 區模組
- [radar-chart.js](file:///c:/Users/TMP-214/Desktop/cji102_project/project_new/js/components/radar-chart.js) - 雷達圖元件
