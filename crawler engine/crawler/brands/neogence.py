# crawler/brands/neogence.py
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crawler.engine.models import Product

BRAND = "neogence"
DOMAIN = "https://www.neogence.com.tw"

# 🔑 人工維護的分類入口
CATEGORY_PAGES = {
    "卸妝/潔顏": "https://www.neogence.com.tw/categories/cleansing",
    "化妝水": "https://www.neogence.com.tw/categories/toner",
    "眼霜": "https://www.neogence.com.tw/categories/eyecream",
    "精華液": "https://www.neogence.com.tw/categories/serum",
    "乳液/乳霜": "https://www.neogence.com.tw/categories/cream",
    "面膜": "https://www.neogence.com.tw/categories/allmask",
    "防曬": "https://www.neogence.com.tw/categories/suncream",
}


def _normalize_url(url: str) -> str:
    """移除 query 與 fragment，避免同商品因參數不同而重複"""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _is_product_path(href: str) -> bool:
    """
    Neogence 商品頁典型：/products/<handle>
    排除：/products?xxx, /products/collections, /products/categories... 等非商品頁
    """
    if not href:
        return False
    low = href.lower().strip()

    if "/products/" not in low:
        return False

    if low.startswith("/products?"):
        return False
    if "/products/collections" in low:
        return False
    if "/products/categories" in low:
        return False
    if "/products/search" in low:
        return False

    # /products/ 後面要有 handle
    return re.search(r"/products/[^/?#]+", low) is not None


def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    """
    回傳：(category_key, product_url)
    方式：分類頁掃 a[href]，挑出 /products/<handle> 的商品連結
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        if not html:
            print(f"[NEOGENCE][warn] fetch category failed: {page_url}")
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue

            low = href.lower()
            if low.startswith("#") or low.startswith("javascript:"):
                continue
            if low.startswith("mailto:") or low.startswith("tel:"):
                continue

            if not _is_product_path(href):
                continue

            full_url = href if href.startswith("http") else urljoin(page_url, href)
            full_url = _normalize_url(full_url)

            key = (category, full_url)
            if key in seen:
                continue
            seen.add(key)
            results.append((category, full_url))

    return results


def _parse_jsonld_product(soup: BeautifulSoup) -> dict:
    """嘗試從 JSON-LD 抓商品資料（有的話最穩）"""
    for tag in soup.select('script[type="application/ld+json"]'):
        raw = tag.get_text(strip=True)
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]
        for obj in candidates:
            if not isinstance(obj, dict):
                continue

            t = obj.get("@type")
            is_product = (t == "Product") or (isinstance(t, list) and "Product" in t)
            if is_product:
                return obj

    return {}


def _clean_price_to_digits(price: str | None) -> str | None:
    """把 'NT$1,880' / '1880' 變成 '1880'；若抓不到就回 None"""
    if not price:
        return None
    digits = re.sub(r"[^\d]", "", str(price))
    return digits or None


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    j = _parse_jsonld_product(soup)

    # 品名
    name = (j.get("name") or "").strip()
    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""

    # 價格（JSON-LD offers → meta → DOM）
    price = None
    offers = j.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
    elif isinstance(offers, list) and offers:
        first = offers[0]
        if isinstance(first, dict):
            price = first.get("price") or first.get("lowPrice")

    if price is None:
        meta_price = soup.select_one("meta[property='product:price:amount']")
        if meta_price and meta_price.get("content"):
            price = meta_price["content"].strip()

    if price is None:
        price_el = soup.select_one(
            ".price, .product-price, .price__value, [data-price], [data-product-price]"
        )
        if price_el:
            price = price_el.get_text(strip=True)

    price = _clean_price_to_digits(price)

    # 描述
    description = (j.get("description") or "").strip()
    if not description:
        meta = soup.select_one("meta[property='og:description'], meta[name='description']")
        description = meta.get("content", "").strip() if meta else ""

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,
        description=description,
        url=url,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# =========================
# ✅ CLI Runner entrypoint（照 Clinique 模板加進度）
# =========================
def run(fetcher, stage: str = "stage1"):
    print("[NEOGENCE] run() start")

    category_pages = globals().get("CATEGORY_PAGES", None)
    if not category_pages:
        raise RuntimeError("[NEOGENCE] CATEGORY_PAGES not found")

    print(f"[NEOGENCE] categories: {len(category_pages)}")

    # 1️⃣ 抓商品 URL（這一步最常卡）
    print("[NEOGENCE] fetching product urls by category...")
    pairs = get_product_urls_by_category(fetcher, category_pages)
    print("[NEOGENCE] product urls fetched")

    product_pairs = []
    if isinstance(pairs, dict):
        for cat, urls in pairs.items():
            print(f"[NEOGENCE] category={cat}, urls={len(urls)}")
            for u in urls:
                product_pairs.append((cat, u))
    else:
        product_pairs = list(pairs)

    print(f"[NEOGENCE] total products: {len(product_pairs)}")

    products: list[Product] = []

    # 2️⃣ 逐一抓商品頁（加 index log）
    for idx, (category, url) in enumerate(product_pairs, start=1):
        print(f"[NEOGENCE] ({idx}/{len(product_pairs)}) fetch product: {url}")

        html = fetcher.get(url)
        if not html:
            print(f"[NEOGENCE][warn] fetch failed: {url}")
            continue

        try:
            p = parse_product(html, url, category)
            if p:
                products.append(p)
        except Exception as e:
            print(f"[NEOGENCE][warn] parse failed: {url} ({type(e).__name__}: {e})")
            continue

    print(f"[NEOGENCE] run() finished, products={len(products)}")
    return products
