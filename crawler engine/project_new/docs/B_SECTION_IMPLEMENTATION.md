# B 區總覽頁面實作總結

## 📋 實作完成

成功實作了 **B 區（智能膚況解析）** 總覽頁面的動態資料綁定和視覺設計。

---

## 🎨 最終設計

### **桌面版佈局**

```
┌──────────────────────────────────────────────┐
│  B. 智能膚況解析              [五角雷達圖]   │
│                                              │
│  🔴 黑眼圈 (7.8)                             │
│  🟠 斑 (6.9)                                 │
│                                              │
│  點擊查看詳情 →                              │
└──────────────────────────────────────────────┘
```

**左側（60%）：**
1. 標題「B. 智能膚況解析」
2. Top 2 問題徽章（垂直排列，全寬）
   - 黑眼圈 (7.8) - 紅色漸層
   - 斑 (6.9) - 橘色漸層
3. 「點擊查看詳情 →」按鈕

**右側（40%）：**
- 五角雷達圖（140x110px）

### **手機版佈局**

```
┌────────────────────┐
│ B. 智能膚況解析    │
│                    │
│ 🔴 黑眼圈 (7.8)    │
│ 🟠 斑 (6.9)        │
│                    │
│ 點擊查看詳情 →     │
│                    │
│  [五角雷達圖]      │
│                    │
└────────────────────┘
```

改為上下佈局，內容在上，雷達圖在下。

---

## 💻 技術實作

### 1. **CSS 樣式**

#### B 區左右佈局
```css
.section-card.card-b {
    display: flex;
    gap: 20px;
    align-items: center;
}

/* 左側內容區 */
.card-b .card-left {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* 右側雷達圖 */
.card-b .radar-preview {
    flex-shrink: 0;
    width: 140px;
    height: 110px;
    margin: 0;
}
```

#### 徽章垂直排列
```css
.card-b .top-issues-badges {
    flex-direction: column;
    gap: 8px;
    margin: 8px 0;
}

.card-b .issue-badge {
    width: 100%; /* 全寬 */
}
```

#### 徽章樣式（三種嚴重度）
```css
.issue-badge.severe {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.06));
    border-color: rgba(239, 68, 68, 0.3);
}

.issue-badge.warning {
    background: linear-gradient(135deg, rgba(251, 146, 60, 0.12), rgba(251, 146, 60, 0.06));
    border-color: rgba(251, 146, 60, 0.3);
}

.issue-badge.moderate {
    background: linear-gradient(135deg, rgba(234, 179, 8, 0.12), rgba(234, 179, 8, 0.06));
    border-color: rgba(234, 179, 8, 0.3);
}
```

#### 手機版響應式
```css
@media (max-width: 768px) {
    .section-card.card-b {
        flex-direction: column-reverse; /* 內容在上，雷達圖在下 */
    }

    .card-b .radar-preview {
        width: 100%;
        max-width: 200px;
        height: 150px;
        margin: 0 auto 16px auto;
    }
}
```

---

### 2. **HTML 結構**

```html
<div class="section-card card-b" onclick="showDetail('section-b')">
    <!-- 左側：內容 -->
    <div class="card-left">
        <div class="section-title">B. 智能膚況解析</div>

        <!-- Top 2 問題徽章 -->
        <div class="top-issues-badges" id="top-issues-badges">
            <div class="issue-badge severe">
                <span class="badge-icon">🔴</span>
                <span class="badge-name">黑眼圈</span>
                <span class="badge-score">(7.8)</span>
            </div>
            <div class="issue-badge warning">
                <span class="badge-icon">🟠</span>
                <span class="badge-name">斑</span>
                <span class="badge-score">(6.9)</span>
            </div>
        </div>

        <div class="section-badge">點擊查看詳情 →</div>
    </div>
    
    <!-- 右側：雷達圖 -->
    <div class="radar-preview">
        <canvas id="radar-chart-overview" width="200" height="150"></canvas>
    </div>
</div>
```

---

### 3. **JavaScript 動態更新**

#### 問題類型映射
```javascript
const ISSUE_MAP = {
    wrinkles: { name: '細紋', icon: '📏' },
    spots: { name: '斑', icon: '🟤' },
    acne: { name: '痘痘', icon: '🔴' },
    comedones: { name: '粉刺', icon: '⚪' },
    darkCircles: { name: '黑眼圈', icon: '🌑' }
};
```

#### 嚴重度判斷
```javascript
function getSeverityLevel(score) {
    if (score >= 7) return 'severe';      // 嚴重 (紅色)
    if (score >= 5) return 'warning';     // 警告 (橘色)
    return 'moderate';                     // 中等 (黃色)
}
```

#### 找出 Top 2 問題
```javascript
function getTopIssues(bScores) {
    const issues = Object.keys(ISSUE_MAP).map(key => ({
        key: key,
        name: ISSUE_MAP[key].name,
        icon: ISSUE_MAP[key].icon,
        score: Number(bScores[key] || 0)
    }));

    // 按分數排序，取前 2 名
    return issues.sort((a, b) => b.score - a.score).slice(0, 2);
}
```

#### 更新徽章
```javascript
function updateTopIssuesBadges(result) {
    const badgesContainer = document.getElementById('top-issues-badges');
    const bScores = result?.b_scores;
    
    if (!bScores) return;

    const topIssues = getTopIssues(bScores);

    badgesContainer.innerHTML = topIssues.map(issue => {
        const severity = getSeverityLevel(issue.score);
        return `
            <div class="issue-badge ${severity}">
                <span class="badge-icon">${issue.icon}</span>
                <span class="badge-name">${issue.name}</span>
                <span class="badge-score">(${issue.score.toFixed(1)})</span>
            </div>
        `;
    }).join('');
}
```

---

## 📊 資料格式

### 後端回傳格式（mock_result.json）

```json
{
  "b_scores": {
    "darkCircles": 7.8,
    "acne": 6.1,
    "comedones": 5.4,
    "wrinkles": 4.2,
    "spots": 6.9
  }
}
```

### 自動處理邏輯

1. **排序**：按分數由高到低排序
2. **取前 2 名**：黑眼圈 (7.8)、斑 (6.9)
3. **判斷嚴重度**：
   - 7.8 ≥ 7 → `severe` (紅色)
   - 6.9 ≥ 5 → `warning` (橘色)
4. **渲染徽章**：動態生成 HTML

---

## 🎯 功能特點

### ✅ 已實作功能

1. **動態資料綁定**
   - 從 `b_scores` 自動提取 Top 2 問題
   - 自動判斷嚴重度並套用對應顏色

2. **視覺設計**
   - 左右佈局（桌面版）
   - 徽章垂直排列，全寬顯示
   - 三種嚴重度配色（紅/橘/黃）

3. **響應式設計**
   - 桌面版：左右佈局
   - 手機版：上下佈局（內容在上，圖在下）

4. **互動效果**
   - 徽章 hover 效果（上浮 + 陰影）
   - 點擊卡片跳轉到詳情頁

---

## 🧪 測試方式

### 在瀏覽器控制台測試

```javascript
// 測試不同的 b_scores 資料
const testData = {
    b_scores: {
        wrinkles: 8.5,  // 細紋最嚴重
        spots: 7.2,     // 斑第二嚴重
        acne: 5.1,
        comedones: 4.3,
        darkCircles: 6.0
    }
};

localStorage.setItem('result', JSON.stringify(testData));
location.reload();

// 預期結果：
// 1. 🔴 細紋 (8.5) - severe (紅色)
// 2. 🟠 斑 (7.2) - severe (紅色)
```

---

## 📝 修改的檔案

1. ✅ **result_new.html**
   - 新增 B 區 CSS 樣式（左右佈局、徽章樣式）
   - 修改 B 區 HTML 結構
   - 新增 JavaScript 函數（getTopIssues、updateTopIssuesBadges 等）
   - 在 loadData() 中調用更新函數

2. ✅ **api/mock_result.json**
   - 已包含 b_scores 測試資料

---

## 🎨 設計亮點

1. **清晰的資訊層級**
   - 標題 → 問題徽章 → 行動按鈕
   - 視覺引導流暢

2. **色彩語意化**
   - 紅色 (severe)：≥7 分，需立即關注
   - 橘色 (warning)：5-7 分，需要注意
   - 黃色 (moderate)：<5 分，輕微問題

3. **空間利用**
   - 左側內容佔 60%（資訊優先）
   - 右側雷達圖佔 40%（視覺輔助）

4. **一致性**
   - 與 A 區的設計語言保持一致
   - 徽章樣式與 A 區的摘要框呼應

---

## ✅ 完成檢查清單

- [x] CSS 左右佈局實作
- [x] 徽章垂直排列樣式
- [x] 三種嚴重度配色
- [x] HTML 結構調整
- [x] JavaScript 動態更新函數
- [x] 手機版響應式設計
- [x] 測試資料準備
- [x] 視覺預覽圖生成

---

**實作完成日期**：2026-01-23  
**版本**：v1.0  
**狀態**：✅ 完成
