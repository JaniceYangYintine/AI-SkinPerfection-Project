"""
AI Skin Analysis System - Database Import Script
=================================================
This script imports data from Excel files to GCP Cloud SQL (MySQL).

Features:
- Connects to GCP Cloud SQL using environment variables
- Imports static data from Excel files
- Handles JSON field conversion
- Provides detailed logging and error handling
- Supports both local and GCP Cloud SQL connections

Usage:
    python import_data.py

Requirements:
    pip install pandas openpyxl pymysql python-dotenv
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pymysql
from dotenv import load_dotenv
import os

# Load environment variables from .env file
# First try current directory, then parent directory (project root)
if not load_dotenv():
    # Try parent directory
    parent_env = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=parent_env)


class DatabaseImporter:
    """Handles database connection and data import operations."""

    def __init__(self):
        """Initialize database connection parameters from environment variables."""
        self.host = os.getenv("GCP_HOST", "localhost")
        self.port = int(os.getenv("GCP_PORT", "3306"))
        self.user = os.getenv("GCP_USER", "root")
        self.password = os.getenv("GCP_PASSWORD", "")
        self.database = os.getenv("GCP_DB_NAME", "skin_perfection_db")
        self.connection = None

    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
            print(f"✅ Connected to database: {self.database} at {self.host}")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            sys.exit(1)

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("✅ Database connection closed")

    def execute_query(self, query: str, params: tuple = None) -> None:
        """Execute a single query."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def import_ingredients(self, file_path: Path) -> int:
        """Import ingredients data from Excel."""
        print("\n📦 Importing ingredients...")
        df = pd.read_excel(file_path)

        query = """
        INSERT INTO ingredients (
            ingredient_id, ingredient_name_zh, ingredient_name_en,
            spot_primary, spot_support, wrinkle_primary, wrinkle_support,
            pore_primary, pore_support, acne_primary, acne_support,
            comedone_primary, comedone_support, dark_circle_primary, dark_circle_support
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        count = 0
        with self.connection.cursor() as cursor:
            for _, row in df.iterrows():
                # Convert ingredient_name_en to JSON string if it's not already
                ingredient_name_en = row["ingredient_name_en"]
                if pd.notna(ingredient_name_en) and not isinstance(ingredient_name_en, str):
                    ingredient_name_en = json.dumps(ingredient_name_en)
                elif pd.notna(ingredient_name_en):
                    # Try to parse if it's already a JSON string
                    try:
                        json.loads(ingredient_name_en)
                    except:
                        # If not valid JSON, wrap it in array
                        ingredient_name_en = json.dumps([ingredient_name_en])

                params = (
                    int(row["ingredient_id"]),
                    row["ingredient_name_zh"],
                    ingredient_name_en,
                    int(row["spot_primary"]),
                    int(row["spot_support"]),
                    int(row["wrinkle_primary"]),
                    int(row["wrinkle_support"]),
                    int(row["pore_primary"]),
                    int(row["pore_support"]),
                    int(row["acne_primary"]),
                    int(row["acne_support"]),
                    int(row["comedone_primary"]),
                    int(row["comedone_support"]),
                    int(row["dark_circle_primary"]),
                    int(row["dark_circle_support"]),
                )
                cursor.execute(query, params)
                count += 1

        self.connection.commit()
        print(f"✅ Imported {count} ingredients")
        return count

    def import_products(self, file_path: Path) -> int:
        """Import products data from Excel."""
        print("\n📦 Importing products...")
        df = pd.read_excel(file_path)

        query = """
        INSERT INTO products (
            product_id, brand, price_tier, category, name, price, description,
            ingredients, concerns, skintypes, sensitivity, anti_aging, moisturizing,
            product_url, image_url, crawled_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        count = 0
        with self.connection.cursor() as cursor:
            for _, row in df.iterrows():
                # Convert JSON fields
                ingredients = self._convert_to_json(row.get("ingredients"))
                concerns = self._convert_to_json(row.get("concerns"))

                # Handle datetime
                crawled_at = row.get("crawled_at")
                if pd.notna(crawled_at):
                    if isinstance(crawled_at, str):
                        crawled_at = datetime.strptime(crawled_at, "%Y-%m-%d %H:%M:%S")
                else:
                    crawled_at = None
                
                # Convert anti_aging and moisturizing (may be 0/1 or Chinese text)
                def to_bool_int(value):
                    if pd.isna(value):
                        return 0
                    if isinstance(value, (int, float)):
                        return int(value)
                    # If it's a string (like '保濕'), treat as 1 if not empty
                    return 1 if str(value).strip() else 0
                
                # Helper to convert NaN to None
                def safe_value(value):
                    return None if pd.isna(value) else value

                params = (
                    int(row["product_id"]),
                    safe_value(row["brand"]),
                    safe_value(row.get("price_tier")),
                    safe_value(row["category"]),
                    safe_value(row["name"]),
                    float(row["price"]) if pd.notna(row.get("price")) else None,
                    safe_value(row.get("description")),
                    ingredients,
                    concerns,
                    safe_value(row.get("skintypes")),
                    safe_value(row.get("sensitivity")),
                    to_bool_int(row.get("anti_aging")),
                    to_bool_int(row.get("moisturizing")),
                    safe_value(row.get("product_url")),
                    safe_value(row.get("image_url")),
                    crawled_at,
                )
                cursor.execute(query, params)
                count += 1

        self.connection.commit()
        print(f"✅ Imported {count} products")
        return count

    def import_product_ingredients(self, file_path: Path) -> int:
        """Import product_ingredients relationship data from Excel."""
        print("\n📦 Importing product-ingredient relationships...")
        df = pd.read_excel(file_path)

        query = """
        INSERT INTO product_ingredients (
            relation_id, ingredient_id, ingredient_name_zh, product_id, category, name, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        count = 0
        with self.connection.cursor() as cursor:
            for _, row in df.iterrows():
                # Handle datetime
                created_at = row.get("created_at")
                if pd.notna(created_at):
                    if isinstance(created_at, str):
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                else:
                    created_at = datetime.now()

                params = (
                    int(row["relation_id"]),
                    int(row["ingredient_id"]),
                    row["ingredient_name_zh"],
                    int(row["product_id"]),
                    row.get("category"),
                    row.get("name"),
                    created_at,
                )
                cursor.execute(query, params)
                count += 1

        self.connection.commit()
        print(f"✅ Imported {count} product-ingredient relationships")
        return count

    def import_actions(self, file_path: Path) -> int:
        """Import actions data from Excel."""
        print("\n📦 Importing actions...")
        df = pd.read_excel(file_path)

        query = """
        INSERT INTO actions (
            action_id, action_name, description, target_issues, gif_url, category
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """

        count = 0
        with self.connection.cursor() as cursor:
            for _, row in df.iterrows():
                # Convert target_issues to JSON
                target_issues = self._convert_to_json(row.get("target_issues"))
                
                # Helper to convert NaN to None
                def safe_value(value):
                    return None if pd.isna(value) else value

                params = (
                    int(row["action_id"]),
                    safe_value(row["action_name"]),
                    safe_value(row.get("description")),
                    target_issues,
                    safe_value(row.get("gif_url")),
                    safe_value(row.get("category")),
                )
                cursor.execute(query, params)
                count += 1

        self.connection.commit()
        print(f"✅ Imported {count} actions")
        return count

    def _convert_to_json(self, value: Any) -> str:
        """Convert value to JSON string."""
        if pd.isna(value):
            return None

        # If already a valid JSON string, return as is
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except:
                # Not valid JSON, try to parse as array
                pass

        # If it's a list or dict, convert to JSON
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)

        # Otherwise, return as string
        return str(value)

    def create_tables(self, sql_file_path: Path) -> None:
        """Create tables from SQL file."""
        print("\n🔨 Creating database tables...")
        
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Remove comments and split by semicolon
            lines = []
            for line in sql_content.split('\n'):
                # Skip comment lines
                if line.strip().startswith('--'):
                    continue
                lines.append(line)
            
            clean_sql = '\n'.join(lines)
            statements = [stmt.strip() for stmt in clean_sql.split(';') if stmt.strip()]
            
            success_count = 0
            error_count = 0
            
            with self.connection.cursor() as cursor:
                for i, statement in enumerate(statements, 1):
                    if not statement:
                        continue
                    try:
                        cursor.execute(statement)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        # Show first 100 chars of failed statement
                        stmt_preview = statement[:100] + '...' if len(statement) > 100 else statement
                        print(f"  ⚠️  Statement {i} failed: {e}")
                        print(f"     SQL: {stmt_preview}")
            
            self.connection.commit()
            
            if error_count == 0:
                print(f"✅ All {success_count} SQL statements executed successfully")
            else:
                print(f"⚠️  {success_count} succeeded, {error_count} failed (tables may already exist)")
                
        except Exception as e:
            print(f"❌ Error reading SQL file: {e}")
            raise

    def clear_tables(self) -> None:
        """Clear all static tables (for re-import)."""
        print("\n🗑️  Clearing existing data...")
        tables = ["product_ingredients", "actions", "products", "ingredients"]

        with self.connection.cursor() as cursor:
            # Disable foreign key checks temporarily
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            for table in tables:
                cursor.execute(f"TRUNCATE TABLE {table}")
                print(f"  ✅ Cleared {table}")

            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        self.connection.commit()


def main():
    """Main import process."""
    print("=" * 70)
    print("AI Skin Analysis System - Database Import")
    print("=" * 70)

    # Get base directory
    base_dir = Path(__file__).resolve().parent

    # File paths
    files = {
        "ingredients": base_dir / "Ingredients.xlsx",
        "products": base_dir / "products.xlsx",
        "product_ingredients": base_dir / "product_ingredients.xlsx",
        "actions": base_dir / "actions.xlsx",
    }

    # Check if all files exist
    missing_files = [name for name, path in files.items() if not path.exists()]
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return 1

    # Initialize importer
    importer = DatabaseImporter()

    try:
        # Connect to database
        importer.connect()

        # Create tables from SQL file
        sql_file = base_dir / "create_tables.sql"
        if sql_file.exists():
            importer.create_tables(sql_file)
        else:
            print("⚠️  Warning: create_tables.sql not found, skipping table creation")

        # Ask user if they want to clear existing data
        response = input("\n⚠️  Clear existing data before import? (y/N): ")
        if response.lower() == "y":
            importer.clear_tables()

        # Import data in order (respecting foreign key constraints)
        total = 0
        total += importer.import_ingredients(files["ingredients"])
        total += importer.import_products(files["products"])
        total += importer.import_product_ingredients(files["product_ingredients"])
        total += importer.import_actions(files["actions"])

        print("\n" + "=" * 70)
        print(f"✅ Import completed successfully! Total records: {total}")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        importer.close()


if __name__ == "__main__":
    sys.exit(main())

# python import_data.py
