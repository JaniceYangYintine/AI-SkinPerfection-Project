# crawler/brands/lancome.py
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup

from crawler.engine.models import Product

BRAND = "lancome"
DOMAIN = "https://www.lancome.com.tw"

# ✅ 依 robots.txt 指向：Sitemap: https://www.lancome.com.tw/sitemap_0.xml
SITEMAP_URL = f"{DOMAIN}/sitemap_0.xml"

# 你要的「分類入口」在蘭蔻站型不一定能完整列出所有商品
# 但為了保持 Runner 介面一致，仍保留這個 dict（實際會被忽略）
CATEGORY_PAGES = {
    "ALL": f"{DOMAIN}/",
}

# ----------------------------
# utils
# ----------------------------
def _normalize_url(url: str) -> str:
    """移除 query 與 fragment，避免同頁因參數不同而重複"""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _clean_price_to_digits(price: str | None) -> str | None:
    """把 'NT$2,500' / '2500' 變成 '2500'；若抓不到就回 None"""
    if not price:
        return None
    digits = re.sub(r"[^\d]", "", str(price))
    return digits or None


def _parse_jsonld_product(soup: BeautifulSoup) -> dict:
    """嘗試從 JSON-LD 抓 Product（最穩）"""
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


def _looks_like_product_page(html: str) -> bool:
    """
    用「是否存在 JSON-LD Product / 常見 PDP 特徵」快速判斷是不是商品頁
    避免 sitemap 裡混到活動頁、客服頁等。
    """
    if not html:
        return False
    # JSON-LD Product
    if '"@type"' in html and "Product" in html and "application/ld+json" in html:
        return True
    # 常見 PDP 字樣（備援）
    if "Old price" in html and "New price" in html:
        return True
    if "產品描述" in html or "產品特色" in html:
        return True
    return False


# ----------------------------
# sitemap -> product urls
# ----------------------------
_SITEMAP_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)

# sitemap 裡常見的非商品頁關鍵字（可再加）
_NON_PRODUCT_HINTS = (
    "/customer-service",
    "/privacy",
    "/security",
    "/official-statement",
    "/stores",
    "/my-account",
    "/account",
    "/cart",
    "/wishlist",
    "/search",
)


def _extract_urls_from_sitemap(xml_text: str) -> list[str]:
    urls = _SITEMAP_LOC_RE.findall(xml_text or "")
    out: list[str] = []
    seen: set[str] = set()

    for u in urls:
        u = u.strip()
        if not u.startswith(DOMAIN):
            continue

        nu = _normalize_url(u)

        # 過濾明顯非商品頁
        low = nu.lower()
        if any(h in low for h in _NON_PRODUCT_HINTS):
            continue

        # 大多商品頁會是 .html（但活動頁也可能是 .html，所以還要二次檢查）
        if not low.endswith(".html"):
            continue

        if nu in seen:
            continue
        seen.add(nu)
        out.append(nu)

    return out


def _guess_category_from_breadcrumb(soup: BeautifulSoup) -> str:
    """
    嘗試從麵包屑推測分類（例：保養 > 臉部保養 / 彩妝 > 唇彩...）
    抓不到就回 '未分類'
    """
    # 常見 breadcrumb 結構：nav/ol/li/a 或 aria-label
    texts: list[str] = []

    # 1) aria-label="breadcrumb"
    bc = soup.select_one('[aria-label="breadcrumb"]')
    if bc:
        for a in bc.select("a, span, li"):
            t = a.get_text(strip=True)
            if t:
                texts.append(t)

    # 2) fallback：常見 class
    if not texts:
        for el in soup.select(".breadcrumb a, .breadcrumb li, .breadcrumbs a, .breadcrumbs li"):
            t = el.get_text(strip=True)
            if t:
                texts.append(t)

    # 清理重複與「首頁」
    cleaned: list[str] = []
    for t in texts:
        if t in ("首頁", "Home"):
            continue
        if t and (not cleaned or cleaned[-1] != t):
            cleaned.append(t)

    # 取前兩層當分類（你也可以改成更多層）
    if len(cleaned) >= 2:
        return f"{cleaned[0]} > {cleaned[1]}"
    if len(cleaned) == 1:
        return cleaned[0]
    return "未分類"


def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    """
    ✅ 保持 Runner 介面一致：回傳 [(category, product_url), ...]
    但蘭蔻改用 sitemap 取得候選商品頁，再逐頁確認是不是 Product。
    """
    xml = fetcher.get(SITEMAP_URL)
    candidates = _extract_urls_from_sitemap(xml)

    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for url in candidates:
        if url in seen:
            continue

        try:
            html = fetcher.get(url)
        except Exception:
            continue

        # 二次檢查：真的像商品頁才收
        if not _looks_like_product_page(html):
            continue

        soup = BeautifulSoup(html, "html.parser")
        j = _parse_jsonld_product(soup)
        if not j:
            # 沒 JSON-LD 也可能是 PDP，但通常不穩；你也可以改成放寬
            continue

        category = _guess_category_from_breadcrumb(soup)
        seen.add(url)
        results.append((category, url))

    return results


# ----------------------------
# product parser
# ----------------------------
def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    j = _parse_jsonld_product(soup)

    # name
    name = (j.get("name") or "").strip()
    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""

    # price
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
        # DOM 備援（站型不同多放一些）
        price_el = soup.select_one(
            ".price, .product-price, .price__value, [data-price], [data-product-price], "
            ".product-price__value, .sales .value, .value[content]"
        )
        if price_el:
            price = price_el.get_text(strip=True)

    price = _clean_price_to_digits(price)

    # description
    description = (j.get("description") or "").strip()
    if not description:
        meta = soup.select_one("meta[property='og:description'], meta[name='description']")
        description = meta.get("content", "").strip() if meta else ""

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,  # 只保留數字字串，例如 "2500"
        description=description,
        url=url,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# ✅ 快速單檔測試（要測再開）
if __name__ == "__main__":
    from crawler.engine.fetch import Fetcher
    f = Fetcher()
    pairs = get_product_urls_by_category(f, CATEGORY_PAGES)
    print("count:", len(pairs))
    print("sample:", pairs[:10])
