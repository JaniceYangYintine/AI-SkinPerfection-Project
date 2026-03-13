import csv
import os
from engine.models import Product

# Standard UTF-8 headers for exported product CSV.
HEADERS = [
    "品牌",
    "產品分類",
    "品名",
    "價格",
    "說明文字",
    "商品網址",
    "圖片網址",
    "爬蟲時間",
]


def write_products_csv(products: list[Product], filepath: str):
    """Write a list of Product to CSV with consistent headers."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        for p in products:
            writer.writerow(
                [
                    getattr(p, "brand", "") or "",
                    getattr(p, "category", "") or "",
                    getattr(p, "name", "") or "",
                    getattr(p, "price", "") or "",
                    getattr(p, "description", "") or "",
                    getattr(p, "url", "") or "",
                    getattr(p, "image_url", "") or "",
                    getattr(p, "crawled_at", "") or "",
                ]
            )
