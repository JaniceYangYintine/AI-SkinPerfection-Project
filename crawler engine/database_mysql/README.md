# Database Deployment Guide

## 📋 Overview

This directory contains enterprise-grade scripts for deploying the AI Skin Analysis database to GCP Cloud SQL (MySQL).

**Files:**
- `create_tables.sql` - SQL schema for all 11 tables
- `import_data.py` - Python script to import Excel data
- `.env.example` - Environment variable template
- `database_schema.md` - Complete schema documentation

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **GCP Cloud SQL** instance created (MySQL 8.0+)
3. **Excel files** in this directory:
   - `Ingredients.xlsx`
   - `products.xlsx`
   - `product_ingredients.xlsx`
   - `actions.xlsx`

### Step 1: Install Dependencies

```bash
pip install pandas openpyxl pymysql python-dotenv
```

### Step 2: Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your database credentials
# Use your favorite text editor
notepad .env  # Windows
```

### Step 3: Create Database Tables

**Option A: Using MySQL Client**
```bash
mysql -h YOUR_GCP_IP -u root -p < create_tables.sql
```

**Option B: Using Python**
```python
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()
connection = pymysql.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

with open('create_tables.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    with connection.cursor() as cursor:
        for statement in sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
    connection.commit()
```

### Step 4: Import Data

```bash
python import_data.py
```

---

## 🔧 GCP Cloud SQL Setup

### 1. Create Cloud SQL Instance

```bash
gcloud sql instances create skin-analysis-db \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=asia-east1 \
    --root-password=YOUR_SECURE_PASSWORD
```

### 2. Create Database

```bash
gcloud sql databases create skin_analysis_db \
    --instance=skin-analysis-db
```

### 3. Configure Network Access

**Option A: Authorize Your IP (Quick)**
```bash
gcloud sql instances patch skin-analysis-db \
    --authorized-networks=YOUR_IP_ADDRESS
```

**Option B: Use Cloud SQL Proxy (Recommended)**
```bash
# Download Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Run proxy (replace CONNECTION_NAME)
./cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME=tcp:3306
```

### 4. Get Connection Info

```bash
gcloud sql instances describe skin-analysis-db
```

---

## 📝 Environment Variables

Create a `.env` file with the following:

```env
# For Public IP connection
DB_HOST=34.80.123.456
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-secure-password
DB_NAME=skin_analysis_db

# For Cloud SQL Proxy
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-secure-password
DB_NAME=skin_analysis_db
```

---

## 🔐 Security Best Practices

### 1. Use Cloud SQL Proxy (Recommended)

Instead of exposing your database with a public IP, use Cloud SQL Proxy:

```bash
# Start proxy in background
./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:3306 &

# In .env, use localhost
DB_HOST=127.0.0.1
```

### 2. Use Secret Manager

Store credentials in GCP Secret Manager instead of `.env`:

```bash
# Create secret
echo -n "your-password" | gcloud secrets create db-password --data-file=-

# Access in Python
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = f"projects/PROJECT_ID/secrets/db-password/versions/latest"
response = client.access_secret_version(request={"name": name})
password = response.payload.data.decode("UTF-8")
```

### 3. Create Read-Only User for Frontend

```sql
-- Create read-only user for frontend team
CREATE USER 'frontend'@'%' IDENTIFIED BY 'frontend-password';
GRANT SELECT ON skin_analysis_db.* TO 'frontend'@'%';
FLUSH PRIVILEGES;
```

---

## 📊 Database Schema

The database consists of **11 tables**:

### Static Tables (4)
1. `ingredients` - 成分表 (35 records)
2. `products` - 產品表 (432 records)
3. `product_ingredients` - 產品成分關聯表 (1,370 records)
4. `actions` - 動作建議表 (10 records)

### Dynamic Tables (7)
5. `users` - 使用者表
6. `sessions` - 分析會話表
7. `questionnaire_answers_tags` - 問卷答案表
8. `session_llm_analysis` - LLM分析結果表
9. `session_skin_scores` - 肌膚評分表
10. `session_recommendations` - 推薦結果表
11. `ga_events` - 使用者行為事件表

See `database_schema.md` for complete documentation.

---

## 🧪 Testing

### Verify Tables Created

```sql
SHOW TABLES;
```

Expected output: 11 tables

### Check Data Import

```sql
SELECT COUNT(*) FROM ingredients;    -- Should be 35
SELECT COUNT(*) FROM products;       -- Should be 432
SELECT COUNT(*) FROM product_ingredients;  -- Should be 1,370
SELECT COUNT(*) FROM actions;        -- Should be 10
```

### Test Foreign Keys

```sql
-- This should work (valid ingredient_id and product_id)
INSERT INTO product_ingredients (ingredient_id, product_id, ingredient_name_zh)
VALUES (1, 1, '玻尿酸');

-- This should fail (invalid ingredient_id)
INSERT INTO product_ingredients (ingredient_id, product_id, ingredient_name_zh)
VALUES (9999, 1, 'test');
```

---

## 🔄 Re-importing Data

If you need to re-import data:

```bash
# The script will ask if you want to clear existing data
python import_data.py

# Or manually clear tables
mysql -h YOUR_HOST -u root -p -e "
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE product_ingredients;
TRUNCATE TABLE actions;
TRUNCATE TABLE products;
TRUNCATE TABLE ingredients;
SET FOREIGN_KEY_CHECKS = 1;
" skin_analysis_db
```

---

## 🐛 Troubleshooting

### Connection Refused

```
Error: Can't connect to MySQL server
```

**Solutions:**
1. Check if Cloud SQL instance is running
2. Verify IP is authorized in Cloud SQL
3. Check firewall rules
4. Try using Cloud SQL Proxy

### Foreign Key Constraint Fails

```
Error: Cannot add or update a child row: a foreign key constraint fails
```

**Solution:** Import data in correct order:
1. ingredients
2. products
3. product_ingredients
4. actions

### JSON Field Errors

```
Error: Invalid JSON text
```

**Solution:** The import script handles JSON conversion automatically. If you're importing manually, ensure JSON fields are properly formatted:

```sql
-- Correct
INSERT INTO products (ingredients) VALUES ('["玻尿酸", "維生素C"]');

-- Wrong
INSERT INTO products (ingredients) VALUES ('玻尿酸, 維生素C');
```

---

## 📞 Support

For issues or questions:
1. Check `database_schema.md` for schema details
2. Review error messages in import script output
3. Check GCP Cloud SQL logs in Console

---

## 📚 Additional Resources

- [GCP Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Cloud SQL Proxy Guide](https://cloud.google.com/sql/docs/mysql/sql-proxy)
- [MySQL 8.0 Reference](https://dev.mysql.com/doc/refman/8.0/en/)
