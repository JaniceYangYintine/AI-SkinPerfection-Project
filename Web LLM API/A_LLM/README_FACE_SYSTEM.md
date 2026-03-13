# A_LLM 面部動作建議系統 - 修改說明

## 修改概述

已成功將 A_LLM 從 AI 生成健康建議改為**基於 face.json 的面部動作隨機選擇系統**。

## 主要變更

### 1. 新增功能模組

#### 載入面部動作資料
```python
# 自動載入 face.json
FACE_DATA_FILE = "face.json"
FACE_ACTIONS = [...] # 10 個面部動作
```

#### 核心函數

**`get_random_face_action()`**
- 從 face.json 隨機選擇一個面部動作
- 返回格式化的建議文本，包含：
  - 針對問題
  - 立即行動方案
  - 預期效果
  - 小提示

**`analyze_face_data(user_data)`**
- 分析用戶資料（目前實作：隨機選擇）
- 未來可擴展為智能選擇：
  - 壓力大 → 眉心放鬆、呼吸相關動作  
  - 睡眠不足 → 眼部放鬆動作
  - 膚質問題 → 血液循環相關動作

**`get_face_advice(user_input_data)`**
- 主要入口函數
- 返回 (user_info, advice) 元組

### 2. 輸出格式

A_LLM 現在會返回以下格式的建議：

```
###面部改善建議

🎯 針對問題：[隨機選擇的問題]

###立即行動方案
[具體動作說明]

###預期效果
[預期的改善效果]

###小提示 ✨
這個動作簡單易行，可以隨時隨地進行。建議每天練習 2-3 次，持續一週後即可看到明顯改善！
```

### 3. 日誌記錄

- 模型名稱：`face-action-selector`
- Prompt 記錄：用戶資料的 JSON 格式

## A_LLM vs C_LLM 差異

| 特性 | A_LLM | C_LLM |
|------|-------|-------|
| 建議來源 | face.json 隨機選擇 | AI 生成 (Gemini) |
| 建議類型 | 面部動作改善 | 飲食控管與臉部保養 |
| 輸出格式 | 單一動作詳細說明 | 多類別建議（生活、營養、飲食、作息、保養） |
| 可預測性 | 從固定的 10 個動作中隨機選擇 | AI 每次生成不同內容 |
| 依賴 | face.json 文件 | Gemini API |

## face.json 內容

包含 10 個面部動作：
1. 面部明暗分布
2. 面部紅潤度
3. 神經肌肉張力
4. 眼神聚焦感
5. 組織水分感
6. 面部輪廓線
7. 眉心緊縮度
8. 鼻翼呼吸感
9. 頸部線條
10. 眼神透亮度

每個動作包含：
- `id`: 編號
- `target_issue`: 針對問題
- `action`: 具體動作
- `effect`: 預期效果

## 系統運作流程

1. 用戶提交問卷 → A_LLM API (Port 5001)
2. A_LLM 讀取 face.json
3. 隨機選擇一個面部動作
4. 格式化輸出建議
5. 返回給前端顯示

## 測試方式

### 啟動 A_LLM
```bash
cd C:\Users\TMP-214\Desktop\ALL_LLM\A_LLM
python api.py
```

### 測試端點
```bash
curl http://localhost:5001/api/test
```

### 測試建議生成
使用統一前端（Port 9000）提交問卷，查看 A_LLM 的輸出。

每次提交都會隨機選擇不同的面部動作（10選1），因此可能需要多次測試才能看到所有動作。

## 未來擴展方向

### 智能選擇邏輯

可以根據用戶數據智能選擇動作：

```python
def analyze_face_data(user_data):
    # 壓力相關
    if user_data.get('stress') == '經常覺得壓力大':
        # 優先選擇眉心緊縮度(7)、鼻翼呼吸感(8)
        candidates = [a for a in FACE_ACTIONS if a['id'] in [7, 8]]
    
    # 睡眠相關
    elif user_data.get('sleep') == '少於6小時':
        # 優先選擇眼神相關(4, 10)
        candidates = [a for a in FACE_ACTIONS if a['id'] in [4, 10]]
    
    # 膚質相關
    elif '乾性' in user_data.get('skin_type', ''):
        # 優先選擇水分相關(5)、血液循環(2)
        candidates = [a for a in FACE_ACTIONS if a['id'] in [2, 5]]
    
    else:
        candidates = FACE_ACTIONS
    
    return random.choice(candidates)
```

### 多動作推薦

可以返回多個相關動作：

```python
def get_multiple_actions(user_data, count=3):
    selected = random.sample(FACE_ACTIONS, min(count, len(FACE_ACTIONS)))
    # 格式化為列表輸出
```

### 用戶回饋系統

記錄用戶對每個動作的反饋，用於優化推薦。

## 注意事項

1. **face.json 必須存在**：確保 `A_LLM/face.json` 文件存在且格式正確
2. **隨機性**：每次請求都是隨機選擇，無法保證特定順序
3. **編碼**：使用 UTF-8 編碼讀取，確保中文正常顯示
4. **錯誤處理**：如果 face.json 載入失敗，會返回錯誤訊息

## 驗證檢查清單

- [x] A_LLM api.py 修改完成
- [x] face.json 文件存在
- [x] 隨機選擇邏輯正確
- [x] 輸出格式符合前端要求
- [ ] 實際啟動測試
- [ ] 提交問卷測試
- [ ] 驗證日誌記錄
- [ ] 檢查與 C_LLM 的差異性
