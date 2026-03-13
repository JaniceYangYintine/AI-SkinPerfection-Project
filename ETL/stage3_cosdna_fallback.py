#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 5B: 從 CosDNA 補充官網沒有的成分資料
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import logging
from pathlib import Path
from urllib.parse import quote

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CosDNAScraper:
    def __init__(self):
        self.search_url = "https://www.cosdna.com/cht/product.php"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        self.session = requests.Session()
        
    def search_product(self, brand, product_name):
        """
        在 CosDNA 搜尋產品
        回傳: (product_url, product_date) 或 (None, None)
        """
        try:
            # 組合搜尋詞：品牌 + 產品名稱
            search_query = f"{brand} {product_name}"
            
            # CosDNA 搜尋參數
            params = {
                'q': search_query,
                'sort': ''
            }
            
            logger.info(f"搜尋: {search_query}")
            response = self.session.get(self.search_url, params=params, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找產品連結（格式: /cht/cosmetic_xxxxxx.html）
            product_links = soup.find_all('a', href=re.compile(r'/cht/cosmetic_[a-f0-9]+\.html'))
            
            if not product_links:
                logger.warning(f"找不到搜尋結果")
                return None, None
            
            # 取第一個結果
            first_link = product_links[0]
            product_url = f"https://www.cosdna.com{first_link['href']}"
            
            # 嘗試抓取產品日期
            date_text = None
            parent = first_link.find_parent(['div', 'li', 'tr', 'td'])
            if parent:
                # 尋找日期樣式的文字（6位數字 YYMMDD）
                date_match = re.search(r'\b(\d{6})\b', parent.get_text())
                if date_match:
                    date_text = date_match.group(1)
            
            logger.info(f"✓ 找到產品: {product_url}")
            if date_text:
                logger.info(f"  日期: {date_text}")
            
            return product_url, date_text
            
        except Exception as e:
            logger.error(f"搜尋失敗: {e}")
            return None, None
    
    def scrape_ingredients(self, product_url, debug=False):
        """
        從 CosDNA 產品頁面抓取成分（英文名稱）
        回傳: 成分字串（只有英文成分名稱，逗號分隔）
        """
        try:
            response = self.session.get(product_url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # DEBUG: 儲存 HTML 以便檢查
            if debug:
                debug_file = "debug_cosdna.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                logger.info(f"DEBUG: 已儲存 HTML 到 {debug_file}")
            
            ingredients = []
            
            # 方法1: 找 class="colors font-semibold break-words"
            ingredient_spans = soup.find_all('span', class_='colors')
            logger.info(f"DEBUG: 找到 {len(ingredient_spans)} 個 colors span")
            
            if ingredient_spans:
                for span in ingredient_spans:
                    # 檢查是否包含 font-semibold
                    if 'font-semibold' in span.get('class', []):
                        ingredient_name = span.get_text().strip()
                        if ingredient_name:
                            ingredients.append(ingredient_name)
                            if debug and len(ingredients) <= 3:
                                logger.info(f"DEBUG: 成分 = {ingredient_name}")
            
            # 方法2: 如果方法1失敗，用正則找
            if not ingredients:
                logger.info("DEBUG: 方法1失敗，嘗試方法2")
                # 找所有 <li> 裡面的第一個連結文字
                lis = soup.find_all('li', class_=re.compile(r'grid.*grid-cols'))
                logger.info(f"DEBUG: 找到 {len(lis)} 個 li 元素")
                
                for li in lis:
                    # 在每個 li 中找第一個連結
                    link = li.find('a', class_='linkb1')
                    if link:
                        # 在連結中找 span
                        spans = link.find_all('span')
                        for span in spans:
                            text = span.get_text().strip()
                            # 如果是英文開頭，可能是成分名稱
                            if text and re.match(r'^[A-Za-z]', text):
                                ingredients.append(text)
                                if debug and len(ingredients) <= 3:
                                    logger.info(f"DEBUG: 成分 = {text}")
                                break
            
            if not ingredients:
                logger.warning(f"找不到成分")
                return None
            
            # 用逗號分隔成分
            ingredients_str = ', '.join(ingredients)
            logger.info(f"✓ 抓取到 {len(ingredients)} 個成分")
            
            return ingredients_str
            
        except Exception as e:
            logger.error(f"抓取成分失敗: {e}")
            return None
    
    def get_ingredients_from_cosdna(self, brand, product_name, debug=False):
        """
        完整流程：搜尋 + 抓取成分
        回傳: (ingredients, date)
        """
        # Step 1: 搜尋產品
        product_url, date = self.search_product(brand, product_name)
        
        if not product_url:
            return None, None
        
        # 禮貌性延遲
        time.sleep(1)
        
        # Step 2: 抓取成分
        ingredients = self.scrape_ingredients(product_url, debug=debug)
        
        return ingredients, date


def main(input_file, output_file):
    """主程式"""
    logger.info("=== Stage 5B: 開始從 CosDNA 補充成分 ===")
    
    # 讀取 Stage 5A 的輸出
    df = pd.read_excel(input_file)
    logger.info(f"讀取 {len(df)} 筆產品資料")
    
    # 找出 ingredients_official 為空的產品
    df_empty = df[df['ingredients_official'].isna()].copy()
    logger.info(f"需要從 CosDNA 補充: {len(df_empty)} 筆")
    
    # 新增欄位儲存 CosDNA 成分和日期
    if 'ingredients_cosdna' not in df.columns:
        df['ingredients_cosdna'] = None
    if 'cosdna_date' not in df.columns:
        df['cosdna_date'] = None
    
    # 初始化爬蟲
    scraper = CosDNAScraper()
    
    # 統計
    success_count = 0
    fail_count = 0
    
    # 開始爬取
    for idx, row in df_empty.iterrows():
        brand = row['品牌']
        product_name = row['品名']
        
        logger.info(f"\n處理 [{success_count + fail_count + 1}/{len(df_empty)}] {brand} - {product_name}")
        
        # 第一個產品開啟 DEBUG
        debug_mode = (success_count + fail_count == 0)
        
        # 從 CosDNA 抓取
        ingredients, date = scraper.get_ingredients_from_cosdna(brand, product_name, debug=debug_mode)
        
        if ingredients:
            df.at[idx, 'ingredients_cosdna'] = ingredients
            if date:
                df.at[idx, 'cosdna_date'] = date
            success_count += 1
            logger.info(f"✓ 成功補充成分")
        else:
            fail_count += 1
            logger.warning(f"✗ CosDNA 也找不到")
        
        # 如果是第一個產品，暫停讓你檢查
        if debug_mode:
            logger.info("\n=== DEBUG 模式：第一個產品已完成 ===")
            logger.info("請檢查 debug_cosdna.html 檔案")
            logger.info("按 Enter 繼續...")
            input()
        
        # 禮貌性延遲（避免被封鎖）
        time.sleep(2)
    
    # 儲存結果
    df.to_excel(output_file, index=False, engine='openpyxl')
    logger.info(f"\n=== 補充完成 ===")
    logger.info(f"成功: {success_count} 筆")
    logger.info(f"失敗: {fail_count} 筆")
    if success_count + fail_count > 0:
        logger.info(f"總完成率: {(success_count/(success_count+fail_count)*100):.1f}%")
    logger.info(f"結果已儲存至: {output_file}")
    
    # 生成報告
    report = df[df['ingredients_official'].isna()].copy()
    report['CosDNA結果'] = report.apply(
        lambda r: '成功' if pd.notna(r['ingredients_cosdna']) else '失敗', 
        axis=1
    )
    
    report_file = output_file.replace('.xlsx', '_report.xlsx')
    report[['品牌', '品名', 'cosdna_date', 'CosDNA結果']].to_excel(
        report_file, index=False, engine='openpyxl'
    )
    logger.info(f"詳細報告: {report_file}")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent / "output"
    candidates = list(base_dir.glob("stageX_official_ingredients_*.xlsx"))
    if not candidates:
        raise FileNotFoundError("找不到 stageX_official_ingredients_*.xlsx")

    input_file = str(max(candidates, key=lambda p: p.stat().st_mtime))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = str(base_dir / f"stageX_cosdna_{timestamp}.xlsx")

    main(input_file, output_file)