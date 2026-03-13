---
name: Data Processor
description: 處理爬蟲資料的合併、清理和轉換工作
---

# Data Processor Skill

這個 skill 專門用於處理爬蟲專案中的資料處理任務。

## 功能

### 1. 資料合併 (Data Merging)
- 合併多個 JSON 檔案
- 處理重複資料
- 驗證資料完整性

### 2. 資料清理 (Data Cleaning)
- 移除空值或無效資料
- 標準化資料格式
- 處理編碼問題
- 提取關鍵成分標籤

### 3. 資料轉換 (Data Transformation)
- JSON 轉 CSV
- JSON 轉 SQL INSERT 語句
- 資料結構重組
- 欄位映射

### 4. 匯入資料庫
- 將清理後的資料匯入 MySQL
- 驗證匯入結果

## 使用方式

當使用者要求以下任務時，使用此 skill：
- "合併爬蟲資料"
- "清理產品資料"
- "匯入產品到資料庫"
- "提取成分標籤"
- "轉換資料格式"

## 執行步驟

### 資料合併流程
1. 掃描 `crawler/output/` 目錄中的所有 JSON 檔案
2. 讀取並解析每個檔案
3. 根據唯一鍵值（如 `product_url`）去重
4. 合併所有資料
5. 輸出到 `crawler/merged/products_merged.json`

**Python 範例**：
```python
import json
from pathlib import Path

def merge_crawler_data(input_dir, output_file):
    all_products = {}
    
    for json_file in Path(input_dir).glob('*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for product in data:
                url = product.get('product_url')
                if url:
                    all_products[url] = product
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(list(all_products.values()), f, ensure_ascii=False, indent=2)
    
    print(f"Merged {len(all_products)} unique products")
```

### 資料清理流程
1. 載入合併後的資料檔案
2. 檢查必要欄位（brand, name, price）
3. 移除或修正無效資料
4. 標準化價格格式（移除貨幣符號）
5. 清理 HTML 標籤
6. 儲存清理後的資料

**檢查清單**：
- ✅ `brand` 不為空
- ✅ `name` 不為空
- ✅ `price` 為有效數字
- ✅ `image_url` 為有效 URL
- ✅ `description` 移除 HTML 標籤

### 成分標籤提取流程
1. 讀取產品資料
2. 從 `ingredients` 或 `description` 欄位提取文字
3. 使用關鍵字清單（keywords）比對
4. 移除停用詞（stop words）
5. 儲存成分標籤到新欄位 `ingredient_tags`

**關鍵字範例**：
- 保濕：玻尿酸、神經醯胺、甘油
- 美白：維他命C、菸鹼醯胺、熊果素
- 抗老：A醇、胜肽、輔酶Q10

### 匯入資料庫流程
1. 連接 MySQL 資料庫
2. 讀取清理後的 JSON 資料
3. 轉換為 SQL INSERT 語句
4. 批次插入到 `products` 表
5. 處理成分關聯（`product_ingredients` 表）
6. 驗證匯入筆數

**Python 範例**：
```python
import mysql.connector
import json

def import_to_database(json_file, db_config):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    for product in products:
        sql = """
        INSERT INTO products (brand, name, price, image_url, product_url, description, price_tier)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            product['brand'],
            product['name'],
            product.get('price'),
            product.get('image_url'),
            product.get('product_url'),
            product.get('description'),
            'counter' if product.get('price', 0) > 1000 else 'drugstore'
        )
        cursor.execute(sql, values)
    
    conn.commit()
    print(f"Imported {len(products)} products")
    cursor.close()
    conn.close()
```

## 目錄結構

```
crawler/
├── output/              # 原始爬蟲資料
│   ├── drwu.json
│   ├── loreal.json
│   └── ...
├── merged/             # 合併後的資料
│   └── products_merged.json
├── cleaned/            # 清理後的資料
│   └── products_cleaned.json
└── stage2_merge.py     # 合併腳本
```

## 最佳實踐

- ✅ 處理前先備份原始資料
- ✅ 記錄處理過程和統計資訊
- ✅ 驗證輸出結果
- ✅ 提供詳細的錯誤訊息
- ✅ 使用 UTF-8 編碼處理中文

## 常見問題

### Q: 如何處理重複的產品？
A: 使用 `product_url` 作為唯一鍵值，後出現的資料會覆蓋先前的。

### Q: 價格格式不統一怎麼辦？
A: 使用正則表達式提取數字：
```python
import re
price_str = "NT$ 1,200"
price = float(re.sub(r'[^\d.]', '', price_str))
```

### Q: 如何判斷開架/專櫃？
A: 根據價格：價格 > 1000 為專櫃，否則為開架。

