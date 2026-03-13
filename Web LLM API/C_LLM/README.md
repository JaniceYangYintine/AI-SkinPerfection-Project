# 健康建議系統 💕

基於 Gemini AI 的健康建議系統,透過問卷收集用戶資訊,提供個人化的健康與保養建議。

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定 API 金鑰
在 `key.env` 檔案中設定您的 Gemini API 金鑰:
```
GEMINI_API_KEY=您的API金鑰
```

### 3. 啟動系統
雙擊 `start.bat` 即可一鍵啟動!

或手動啟動:
```bash
# 啟動後端 API
python api.py

# 另開一個終端,啟動前端
python frontend_server.py
```

### 4. 開啟網頁
在瀏覽器輸入: http://localhost:8080

---

## 📂 專案結構

```
LLM/
├── api.py              # 後端 API 伺服器 (Flask + Gemini AI)
├── frontend_server.py  # 前端 HTTP 伺服器
├── index.html          # 前端網頁介面
├── start.bat           # 一鍵啟動腳本
├── cleanup_ports.bat   # Port 清理腳本
├── requirements.txt    # Python 依賴套件
├── key.env             # API 金鑰設定 (需自行配置)
├── logs/               # 日誌目錄
│   ├── history.json    # 問卷與 AI 回應記錄
│   └── 格式說明.md     # 日誌格式說明
└── 快速開始.md         # 快速入門指南
```

---

## 🔧 功能特色

### 🌐 前端網頁
- 美觀的問卷表單介面
- API 連線狀態即時顯示
- **測試功能**: 快速填充 / 隨機填充按鈕
- 響應式設計

### 🤖 後端 API
- 使用 Gemini 2.5 Flash 模型
- 完整的 CORS 支援
- RESTful API 設計

### 📊 日誌記錄
- 自動記錄每次問卷提交
- 記錄完整的 prompt 和 AI 回應
- JSON 格式,易於分析

---

## 📝 API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/health-advice` | POST | 提交問卷,獲取 AI 健康建議 |
| `/api/test` | GET | API 連線測試 |

### 請求範例
```json
POST /api/health-advice
{
  "age": "25歲",
  "skin_type": "混合性肌膚(T字出油兩頰乾)",
  "sensitivity": "不太會",
  "skincare_routine": "早晚完整保養",
  "sleep": "7-8小時",
  "stress": "偶爾覺得有",
  "exercise": "3-4天",
  "fried_food": "0-1次",
  "veggies": "每天都有吃"
}
```

---

## ⚠️ 常見問題

### Port 佔用錯誤
如果出現「一次只能用一個通訊端位址」錯誤:
1. 執行 `cleanup_ports.bat`
2. 重新執行 `start.bat`

### API 連線失敗
1. 確認 `key.env` 中的 API 金鑰正確
2. 確認後端 API 已啟動
3. 檢查網路連線

---

## 🛠️ 技術棧

- **前端**: HTML5, CSS3, JavaScript
- **後端**: Python, Flask
- **AI**: Google Gemini 2.5 Flash
- **資料儲存**: JSON

---

## 📄 授權

此專案僅供學習和個人使用。
