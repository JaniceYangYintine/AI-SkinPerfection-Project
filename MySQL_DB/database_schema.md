# AI SkinPerfection Database Schema

本文件說明 AI SkinPerfection 系統的資料庫設計，包含靜態資料表與動態資料表。

---

# 靜態資料表 (Static Tables)

## 1. ingredients（成分表）

用途：儲存保養品成分資料，以及其對六種肌膚問題的功效。

| 欄位名稱 | 資料型態 | 約束條件 | 說明 |
|---|---|---|---|
| ingredient_id | INT | PRIMARY KEY, AUTO_INCREMENT | 成分唯一識別碼 |
| ingredient_name_zh | VARCHAR(100) | NOT NULL, UNIQUE | 成分中文名稱 |
| ingredient_name_en | JSON | NULL | 成分英文名稱（陣列） |
| spot_primary | TINYINT(1) | DEFAULT 0 | 斑點主要功效 |
| spot_support | TINYINT(1) | DEFAULT 0 | 斑點輔助功效 |
| wrinkle_primary | TINYINT(1) | DEFAULT 0 | 皺紋主要功效 |
| wrinkle_support | TINYINT(1) | DEFAULT 0 | 皺紋輔助功效 |
| pore_primary | TINYINT(1) | DEFAULT 0 | 毛孔主要功效 |
| pore_support | TINYINT(1) | DEFAULT 0 | 毛孔輔助功效 |
| acne_primary | TINYINT(1) | DEFAULT 0 | 痘痘主要功效 |
| acne_support | TINYINT(1) | DEFAULT 0 | 痘痘輔助功效 |
| comedone_primary | TINYINT(1) | DEFAULT 0 | 粉刺主要功效 |
| comedone_support | TINYINT(1) | DEFAULT 0 | 粉刺輔助功效 |
| dark_circle_primary | TINYINT(1) | DEFAULT 0 | 黑眼圈主要功效 |
| dark_circle_support | TINYINT(1) | DEFAULT 0 | 黑眼圈輔助功效 |

---

## 2. products（產品表）

用途：儲存保養品產品資訊。

| 欄位名稱 | 資料型態 | 約束條件 | 說明 |
|---|---|---|---|
| product_id | INT | PRIMARY KEY, AUTO_INCREMENT | 產品唯一識別碼 |
| brand | VARCHAR(100) | NOT NULL | 品牌 |
| price_tier | VARCHAR(20) | NULL | 價格區間 |
| category | VARCHAR(50) | NOT NULL | 產品類別 |
| name | VARCHAR(255) | NOT NULL | 產品名稱 |
| price | DECIMAL(10,2) | NULL | 價格 |
| description | TEXT | NULL | 產品描述 |
| ingredients | JSON | NULL | 成分列表 |
| concerns | JSON | NULL | 適用肌膚問題 |
| skintypes | VARCHAR(100) | NULL | 適用膚質 |
| sensitivity | VARCHAR(50) | NULL | 敏感肌適用性 |
| anti_aging | TINYINT(1) | DEFAULT 0 | 抗老 |
| moisturizing | TINYINT(1) | DEFAULT 0 | 保濕 |
| product_url | VARCHAR(500) | NULL | 產品頁面 |
| image_url | VARCHAR(500) | NULL | 產品圖片 |
| crawled_at | TIMESTAMP | NULL | 爬蟲時間 |

---

## 3. product_ingredients（產品成分關聯表）

用途：紀錄產品與成分的多對多關係。

| 欄位名稱 | 資料型態 | 約束條件 | 說明 |
|---|---|---|---|
| ingredient_id | INT | PK | 成分 ID |
| ingredient_name_zh | VARCHAR(100) | NOT NULL | 成分名稱 |
| product_id | INT | PK | 產品 ID |
| category | VARCHAR(50) | NULL | 產品類別 |
| name | VARCHAR(255) | NULL | 產品名稱 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 建立時間 |

複合主鍵：
