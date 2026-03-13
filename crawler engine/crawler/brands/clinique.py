# crawler/brands/clinique.py
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crawler.engine.models import Product

BRAND = "clinique"
DOMAIN = "https://www.clinique.com.tw"

# 🔑 人工維護的分類入口（你之後要加/改分類就改這裡）
# 這些是 Clinique 官網導覽列常見入口（分類頁內會有 /product/... 的商品連結）
CATEGORY_PAGES = {
    "清潔/卸妝": "https://www.clinique.com.tw/products/1673/skincare/cleansers_makeup_removers",
    "潔膚水/角質調理": "https://www.clinique.com.tw/products/1682/skincare/exfoliators_masks",
    "精華露/化妝水": "https://www.clinique.com.tw/essence-lotions",
    "臉部精華液": "https://www.clinique.com.tw/products/4034/skincare/serums",
    "乳液/乳霜/面膜": "https://www.clinique.com.tw/moisturizers",
    "眼唇保養": "https://www.clinique.com.tw/products/1683/skin-care/eye-care",
    "防曬隔離": "https://www.clinique.com.tw/sunscreen-primer",
}


def _normalize_url(url: str) -> str:
    """移除 query 與 fragment，避免同商品因參數不同而重複"""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _is_product_path(href: str) -> bool:
    """
    Clinique 商品頁典型：/product/<cat_id>/<prod_id>/.../<slug>
    分類頁典型：/products/<id>/...（注意：products 是分類，不是商品）
    """
    if not href:
        return False
    low = href.strip().lower()

    # 只抓商品頁
    if "/product/" not in low:
        return False

    # 排除一些可能的非商品頁
    if low.startswith("/product?"):
        return False
    if "/product/" in low and low.endswith("/"):
        # 仍可能是商品，但多數商品不會只有 /product/ 結尾；保守排除
        # 你若遇到真的商品以 / 結尾，可把這段刪掉
        pass

    # 基本形狀：/product/數字/數字/...
    return re.search(r"/product/\d+/\d+/", low) is not None


def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    """
    回傳：(category_key, product_url)
    方式：把分類頁上所有 a[href] 掃過，挑出 /product/... 連結
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
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

            # 只收本域名
            if urlparse(full_url).netloc and DOMAIN not in full_url:
                continue

            key = (category, full_url)
            if key in seen:
                continue
            seen.add(key)
            results.append((category, full_url))

    return results


def _parse_jsonld_product(soup: BeautifulSoup) -> dict:
    """嘗試從 JSON-LD 抓商品資料（若站有提供會最穩）"""
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
    """把 'NT$1,900' / '1900' 變成 '1900'；若抓不到就回 None"""
    if not price:
        return None
    digits = re.sub(r"[^\d]", "", str(price))
    return digits or None


def _extract_price_fallback(soup: BeautifulSoup) -> str | None:
    """
    Clinique 商品頁常見會出現：NT$1,900
    我們直接從整頁文字撈第一個 NT$ 價格當備援
    """
    text = soup.get_text(" ", strip=True)
    m = re.search(r"NT\$\s*[\d,]+", text)
    return m.group(0) if m else None


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    j = _parse_jsonld_product(soup)

    # 品名
    name = (j.get("name") or "").strip()
    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""

    # 描述（JSON-LD → meta → Product Details 附近）
    description = (j.get("description") or "").strip()
    if not description:
        meta = soup.select_one("meta[property='og:description'], meta[name='description']")
        description = meta.get("content", "").strip() if meta else ""

    if not description:
        # Product Details 後面常有一段描述（抓第一個比較像段落的句子）
        text = soup.get_text("\n", strip=True)
        # 找 "Product Details" 後 1~2 行
        m = re.search(r"Product Details\s+(.{10,200})", text, flags=re.S)
        if m:
            description = m.group(1).strip().split("\n")[0].strip()

    # 價格（JSON-LD offers → fallback regex）
    price = None
    offers = j.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
    elif isinstance(offers, list) and offers:
        first = offers[0]
        if isinstance(first, dict):
            price = first.get("price") or first.get("lowPrice")

    if price is None:
        price = _extract_price_fallback(soup)

    price = _clean_price_to_digits(price)

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,  # 只留數字字串，例如 "1900"
        description=description,
        url=url,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# ✅ 快速單檔測試（你要測再打開）
if __name__ == "__main__":
    from crawler.engine.fetch import Fetcher
    f = Fetcher()
    pairs = get_product_urls_by_category(f, {"清潔/卸妝": CATEGORY_PAGES["清潔/卸妝"]})
    print("count:", len(pairs))
    print("sample:", pairs[:10])

# =========================
# ✅ CLI Runner entrypoint（含進度紀錄）
# =========================
def run(fetcher, stage: str = "stage1"):
    print("[CLINIQUE] run() start")

    category_pages = globals().get("CATEGORY_PAGES", None)
    if not category_pages:
        raise RuntimeError("[CLINIQUE] CATEGORY_PAGES not found")

    print(f"[CLINIQUE] categories: {len(category_pages)}")

    # 1️⃣ 抓商品 URL（這一步最常卡）
    print("[CLINIQUE] fetching product urls by category...")
    pairs = get_product_urls_by_category(fetcher, category_pages)
    print("[CLINIQUE] product urls fetched")

    product_pairs = []
    if isinstance(pairs, dict):
        for cat, urls in pairs.items():
            print(f"[CLINIQUE] category={cat}, urls={len(urls)}")
            for u in urls:
                product_pairs.append((cat, u))
    else:
        product_pairs = list(pairs)

    print(f"[CLINIQUE] total products: {len(product_pairs)}")

    products = []

    # 2️⃣ 逐一抓商品頁（加 index log）
    for idx, (category, url) in enumerate(product_pairs, start=1):
        print(f"[CLINIQUE] ({idx}/{len(product_pairs)}) fetch product: {url}")

        html = fetcher.get(url)
        if not html:
            print(f"[CLINIQUE][warn] fetch failed: {url}")
            continue

        try:
            p = parse_product(html, url, category)
            if p:
                products.append(p)
        except Exception as e:
            print(f"[CLINIQUE][warn] parse failed: {url} ({type(e).__name__}: {e})")
            continue

    print(f"[CLINIQUE] run() finished, products={len(products)}")
    return products
