# 前端整合實作清單

> 更新日期: 2026-01-24 22:13

---

## ✅ 已完成

### 1. D 區產品推薦功能
- [x] 實作 `loadSectionDData()` 函數
- [x] 實作 `renderIngredients()` 函數 (成分說明)
- [x] 實作 `renderProducts()` 函數 (產品卡片)
- [x] 實作 `trackProductClick()` 函數 (GA4 追蹤)
- [x] 在 `DOMContentLoaded` 中加入 `loadSectionDData()` 呼叫
- [x] 更新 `mock_result.json` 加入 D 區假資料

### 2. 現有功能
- [x] A 區:氣色分析 (`loadSectionAData`)
- [x] B 區:膚況分析 (`loadSectionBData`)
  - [x] 五角雷達圖
  - [x] Top 2 問題顯示
- [x] C 區:生活建議 (`loadSectionCData`)

### 3. API 整合
- [x] 建立 `js/api-config.js` 配置檔
- [x] 實作 `result_new.html` 的資料載入邏輯
  - [x] `loadResultData()` 函數 (從 API 或 localStorage 載入)
  - [x] `loadFromLocalStorage()` 函數 (降級方案)
  - [x] `loadAllSections()` 函數 (統一載入所有區塊)
  - [x] 修改所有 `loadSection` 函數接收 `result` 參數
- [x] 實作 `survey_new.html` 的提交邏輯
  - [x] 修改 `submitSurvey()` 函數支援 async/await
  - [x] 加入 API 呼叫邏輯
  - [x] 加入開發模式 / 正式環境切換
  - [x] 加入錯誤處理

### 4. Loading 動畫
- [x] 在 `survey_new.html` 加入 Loading 樣式
- [x] 在 `survey_new.html` 加入 Loading HTML
- [x] 實作 `showLoading()` 和 `hideLoading()` 函數

### 5. 測試工具
- [x] 建立 `test_api.html` 測試頁面

### 6. 文檔
- [x] `docs/software_architecture_by_section.md` - 分區軟體架構
- [x] `docs/frontend_implementation_checklist.md` - 前端實作清單
- [x] `docs/architecture.md` - 完整系統架構

---

## ❌ 待實作 (高優先級)

### 1. API 整合

#### 1.1 修改 `survey_new.html` - 提交分析

**位置:** `c:\Users\TMP-214\Desktop\cji102_project\project_new\survey_new.html`

**需要加入:**

```javascript
// 在問卷完成後
async function submitAnalysis() {
    try {
        // 1. 取得 LINE User ID
        const userId = liff.getContext().userId;
        
        // 2. 取得照片和問卷答案
        const photo = localStorage.getItem('photo');
        const answers = [
            document.querySelector('[name="q1"]:checked')?.value,
            document.querySelector('[name="q2"]:checked')?.value,
            // ... 其他 7 題
        ];
        
        // 3. 顯示 Loading
        showLoading('分析中,請稍候...');
        
        // 4. 呼叫 n8n API
        const response = await fetch('https://your-n8n.run.app/webhook/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo: photo,
                line_user_id: userId,
                answers: answers
            })
        });
        
        if (!response.ok) {
            throw new Error('分析失敗');
        }
        
        const result = await response.json();
        
        // 5. 儲存 session_id
        localStorage.setItem('session_id', result.session_id);
        
        // 6. 跳轉到結果頁
        location.href = 'result_new.html';
        
    } catch (error) {
        console.error('提交分析失敗:', error);
        alert('分析失敗,請重試');
        hideLoading();
    }
}
```

#### 1.2 修改 `result_new.html` - 取得結果

**位置:** `c:\Users\TMP-214\Desktop\cji102_project\project_new\result_new.html`

**需要修改:**

```javascript
// 修改 DOMContentLoaded 事件
window.addEventListener('DOMContentLoaded', async () => {
    try {
        // 1. 取得 session_id
        const sessionId = localStorage.getItem('session_id');
        
        if (!sessionId) {
            console.warn('找不到 session_id,使用假資料');
            // 使用 mock 資料
            const mockResult = await fetch('./api/mock_result.json').then(r => r.json());
            loadAllSections(mockResult);
            return;
        }
        
        // 2. 從 GCP Cloud Run 取得結果
        const response = await fetch(`https://your-api.run.app/api/result?session_id=${sessionId}`);
        
        if (!response.ok) {
            throw new Error('取得結果失敗');
        }
        
        const result = await response.json();
        
        // 3. 載入所有區塊
        loadAllSections(result);
        
    } catch (error) {
        console.error('取得結果失敗:', error);
        // 降級使用 mock 資料
        const mockResult = await fetch('./api/mock_result.json').then(r => r.json());
        loadAllSections(mockResult);
    }
});

function loadAllSections(result) {
    loadSectionAData(result);
    loadSectionBData(result);
    loadSectionCData(result);
    loadSectionDData(result);
}
```

### 2. LIFF SDK 整合

#### 2.1 安裝 LIFF SDK

**方法 1: CDN (推薦)**

在 `analyze.html` 和 `survey_new.html` 的 `<head>` 中加入:

```html
<script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
```

**方法 2: npm**

```bash
npm install @line/liff
```

#### 2.2 初始化 LIFF

在 `analyze.html` 或 `survey_new.html` 中加入:

```javascript
// 初始化 LIFF
liff.init({ liffId: 'YOUR_LIFF_ID' })
    .then(() => {
        console.log('LIFF 初始化成功');
        
        // 檢查是否在 LINE 中開啟
        if (!liff.isInClient()) {
            console.warn('請在 LINE 中開啟此頁面');
        }
        
        // 取得 User ID
        const userId = liff.getContext().userId;
        console.log('LINE User ID:', userId);
        
        // 儲存到 localStorage (供後續使用)
        localStorage.setItem('line_user_id', userId);
    })
    .catch((err) => {
        console.error('LIFF 初始化失敗:', err);
        alert('初始化失敗,請重新開啟');
    });
```

### 3. Loading 動畫

**建立 Loading 元件:**

```html
<!-- 在 body 最後加入 -->
<div id="loading-overlay" style="display:none;">
    <div class="loading-spinner"></div>
    <p id="loading-text">分析中...</p>
</div>
```

```css
#loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

.loading-spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #D4A574;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

#loading-text {
    color: white;
    margin-top: 20px;
    font-size: 16px;
}
```

```javascript
function showLoading(text = '載入中...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    if (overlay) {
        loadingText.textContent = text;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}
```

---

## 📝 待實作 (中優先級)

### 4. GA4 埋點追蹤

**需要加入:**

```javascript
// 在 result_new.html 中加入

// 追蹤變數
let sectionTimers = {};
let clickedProducts = [];
let sessionId = localStorage.getItem('session_id');

// 追蹤區塊開始
function trackSectionStart(sectionName) {
    sectionTimers[sectionName] = Date.now();
    console.log(`📊 開始追蹤 ${sectionName}`);
}

// 追蹤區塊結束
function trackSectionEnd(sectionName) {
    if (sectionTimers[sectionName]) {
        const duration = (Date.now() - sectionTimers[sectionName]) / 1000;
        
        // 發送到 GA4
        if (typeof gtag !== 'undefined') {
            gtag('event', `${sectionName}_duration`, {
                'value': duration,
                'session_id': sessionId
            });
        }
        
        console.log(`📊 ${sectionName} 停留時間: ${duration.toFixed(2)} 秒`);
    }
}

// 在 showDetail 函數中加入追蹤
function showDetail(section) {
    // 追蹤上一個區塊結束
    const currentSection = document.querySelector('.detail-section.active');
    if (currentSection) {
        const sectionName = currentSection.dataset.section;
        trackSectionEnd(`section_${sectionName}`);
    }
    
    // 原有的顯示邏輯
    // ...
    
    // 追蹤新區塊開始
    trackSectionStart(`section_${section}`);
}

// 離開頁面時儲存到資料庫
window.addEventListener('beforeunload', async () => {
    const gaData = {
        session_id: sessionId,
        overview_duration: sectionTimers.overview ? (Date.now() - sectionTimers.overview) / 1000 : 0,
        section_a_duration: sectionTimers.section_a ? (Date.now() - sectionTimers.section_a) / 1000 : 0,
        section_b_duration: sectionTimers.section_b ? (Date.now() - sectionTimers.section_b) / 1000 : 0,
        section_c_duration: sectionTimers.section_c ? (Date.now() - sectionTimers.section_c) / 1000 : 0,
        section_d_duration: sectionTimers.section_d ? (Date.now() - sectionTimers.section_d) / 1000 : 0,
        clicked_products: clickedProducts,
        products_click_count: clickedProducts.length,
        exit_method: 'browser_close',
        exit_time: new Date().toISOString()
    };
    
    // 使用 sendBeacon 確保資料送出
    navigator.sendBeacon('/api/ga-events', JSON.stringify(gaData));
});
```

### 5. 錯誤處理

**建立錯誤處理函數:**

```javascript
function handleError(error, userMessage = '發生錯誤,請稍後再試') {
    console.error('Error:', error);
    
    // 顯示錯誤訊息
    alert(userMessage);
    
    // 記錄到 GA4
    if (typeof gtag !== 'undefined') {
        gtag('event', 'error', {
            'error_message': error.message,
            'error_stack': error.stack
        });
    }
}
```

---

## 🔧 環境變數配置

**建立 `js/config.js`:**

```javascript
// API 配置
export const API_CONFIG = {
    // n8n API
    N8N_ANALYZE_URL: 'https://your-n8n.run.app/webhook/analyze',
    
    // GCP Cloud Run API
    GCP_RESULT_URL: 'https://your-api.run.app/api/result',
    GCP_GA_EVENTS_URL: 'https://your-api.run.app/api/ga-events',
    
    // LIFF
    LIFF_ID: 'YOUR_LIFF_ID',
    
    // 超時設定 (毫秒)
    TIMEOUT: 30000
};

// GA4 配置
export const GA_CONFIG = {
    MEASUREMENT_ID: 'G-XXXXXXXXXX'
};
```

---

## 📊 測試清單

### 本地測試
- [ ] D 區資料正確顯示
- [ ] 成分說明正確渲染
- [ ] 產品卡片正確渲染
- [ ] 產品點擊追蹤正常

### API 整合測試
- [ ] n8n API 呼叫成功
- [ ] GCP API 取得結果成功
- [ ] 錯誤處理正常運作
- [ ] Loading 動畫顯示正常

### LIFF 測試
- [ ] LIFF 初始化成功
- [ ] User ID 取得成功
- [ ] 在 LINE 中正常運作

### GA4 測試
- [ ] 區塊停留時間追蹤
- [ ] 產品點擊追蹤
- [ ] 離開事件追蹤

---

## 🚀 下一步

1. **立即執行:**
   - 實作 API 整合 (survey_new.html + result_new.html)
   - 加入 LIFF SDK
   - 加入 Loading 動畫

2. **後續執行:**
   - 實作 GA4 埋點
   - 完善錯誤處理
   - 進行完整測試

3. **部署前:**
   - 更新 API URL 為正式環境
   - 更新 LIFF ID
   - 更新 GA4 Measurement ID
