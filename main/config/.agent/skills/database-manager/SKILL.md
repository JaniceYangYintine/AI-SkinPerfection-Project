---
name: Database Manager
description: 資料庫管理工具 - 備份、還原、遷移、測試資料匯入
---

# Database Manager Skill

這個 skill 專門用於管理專案的 MySQL 資料庫操作。

## 功能

### 1. 資料庫備份 (Backup)
- 完整備份資料庫
- 備份特定資料表
- 自動加上時間戳記

### 2. 資料庫還原 (Restore)
- 從備份檔案還原
- 驗證資料完整性

### 3. 執行遷移 (Migration)
- 執行 SQL migration 腳本
- 追蹤已執行的 migrations

### 4. 匯入測試資料 (Seed Data)
- 匯入預設的測試資料
- 清空並重新匯入

### 5. 資料庫狀態檢查
- 檢查連線狀態
- 檢查資料表結構
- 統計資料筆數

## 使用方式

當使用者要求以下任務時，使用此 skill：
- "備份資料庫"
- "執行 migration"
- "匯入測試資料"
- "檢查資料庫狀態"
- "還原資料庫"

## 執行步驟

### 資料庫備份流程
1. 檢查 MySQL 連線
2. 讀取 `.env` 檔案取得資料庫設定
3. 使用 `mysqldump` 執行備份
4. 儲存到 `database_mysql/backups/` 目錄
5. 檔名格式：`backup_YYYYMMDD_HHMMSS.sql`

**命令範例**：
```bash
mysqldump -u [username] -p[password] skin_perfection > database_mysql/backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### 執行 Migration 流程
1. 掃描 `database_mysql/migrations/` 目錄
2. 按照檔名順序執行 SQL 腳本
3. 記錄執行結果
4. 如果失敗，提供錯誤訊息

**命令範例**：
```bash
mysql -u [username] -p[password] skin_perfection < database_mysql/migrations/001_optimize_schema.sql
```

### 匯入測試資料流程
1. 檢查是否有 `database_mysql/seeds/` 目錄
2. 執行 seed 腳本
3. 驗證資料是否正確匯入
4. 顯示匯入統計

### 資料庫狀態檢查流程
1. 測試連線
2. 列出所有資料表
3. 顯示每個資料表的筆數
4. 檢查外鍵關聯是否正常

**SQL 範例**：
```sql
-- 檢查資料表筆數
SELECT 
    table_name,
    table_rows
FROM information_schema.tables
WHERE table_schema = 'skin_perfection'
ORDER BY table_name;
```

## 環境變數

需要在 `.env` 檔案中設定：
```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=skin_perfection
```

## 目錄結構

```
database_mysql/
├── migrations/          # Migration 腳本
│   └── 001_optimize_schema.sql
├── seeds/              # 測試資料腳本
│   ├── seed_users.sql
│   ├── seed_products.sql
│   └── seed_ingredients.sql
├── backups/            # 備份檔案（自動建立）
└── DATABASE_SCHEMA.md  # 資料庫架構文件
```

## 最佳實踐

- ✅ **執行 migration 前先備份**
- ✅ **測試資料不要用於正式環境**
- ✅ **定期備份資料庫**
- ✅ **Migration 檔案使用編號前綴（001_, 002_）**
- ✅ **備份檔案保留至少 7 天**

## 常見問題

### Q: 如何連線到 GCP 上的資料庫？
A: 修改 `.env` 中的 `DB_HOST` 為 GCP 的 IP 位址，並確保防火牆規則允許連線。

### Q: Migration 執行失敗怎麼辦？
A: 先還原備份，檢查 SQL 語法，修正後重新執行。

### Q: 如何只備份特定資料表？
A: 使用 `mysqldump` 加上資料表名稱：
```bash
mysqldump -u root -p skin_perfection users sessions > backup_users_sessions.sql
```

## 安全注意事項

- 🔒 **不要將 `.env` 檔案提交到 Git**
- 🔒 **備份檔案可能包含敏感資料，小心處理**
- 🔒 **正式環境的備份要加密儲存**
