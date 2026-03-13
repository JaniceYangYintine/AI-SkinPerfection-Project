"""Crawler for AHC products."""

import json
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "AHC"
BASE_URL = "https://tw.ahcbeauty.com"

# Hard-coded category pages. Keep keys stable for downstream CSVs.
CATEGORY_PAGES: dict[str, str] = {
    "toner-mist": f"{BASE_URL}/collections/%E5%8C%96%E5%A6%9D%E6%B0%B4-%E5%99%B4%E9%9C%A7",
    "serum-ampoule": f"{BASE_URL}/collections/%E7%B2%BE%E8%8F%AF-%E5%AE%89%E7%93%B6",
    "lotion-cream-eye": f"{BASE_URL}/collections/%E4%B9%B3%E6%B6%B2-%E4%B9%B3%E9%9C%9C%E7%9C%BC%E9%9C%9C",
    "suncare": f"{BASE_URL}/collections/%E9%98%B2%E6%9B%AC",
    "cleanser": f"{BASE_URL}/collections/%E6%BD%94%E9%A1%8F",
}


def _normalize_url(url: str) -> str:
    """Drop query parameters to normalize product URLs."""
    return url.split("?", 1)[0]


def _normalize_image_url(url: str | None) -> str | None:
    """Ensure image URL is absolute; keep original size/version (no auto-crop)."""
    if not url:
        return None
    url = url.strip()
    # Raw CDN path like /cdn/shop/files/...
    if url.startswith("/cdn/"):
        url = "https://cdn.shopify.com" + url
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = urljoin(BASE_URL, url)
    return url


def get_product_urls_by_category(
    fetcher, category_pages: dict[str, str]
) -> list[tuple[str, str]]:
    """Return list of (category, product_url) pairs discovered on category pages."""
    results: list[tuple[str, str]] = []
    seen_urls: set[str] = set()  # 只記錄 URL,避免同產品因不同分類而重複

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select('a[href*="/products/"]'):
            href = a.get("href")
            if not href:
                continue

            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            full_url = _normalize_url(full_url)

            # 如果這個 URL 已經爬過了,就跳過
            if full_url in seen_urls:
                continue

            seen_urls.add(full_url)
            results.append((category, full_url))  # 保留第一次出現的分類

    return results


def _extract_price(soup: BeautifulSoup) -> str | None:
    """Try LD+JSON offers first; fallback to meta price tags."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") == "Product":
                offers = item.get("offers")
                if isinstance(offers, list):
                    offers = offers[0] if offers else None
                if isinstance(offers, dict):
                    price = offers.get("price")
                    currency = offers.get("priceCurrency")
                    if price:
                        prefix = "NT$" if currency in (None, "TWD") else f"{currency} "
                        return f"{prefix}{price}"

    meta_price = soup.select_one(
        "meta[property='product:price:amount'], meta[property='og:price:amount']"
    )
    if meta_price and meta_price.get("content"):
        return f"NT${meta_price['content']}"
    return None


def _extract_description(soup: BeautifulSoup) -> str:
    """Collect content-area h2 + rte text first, then other rte blocks; fallback to meta."""
    chunks: list[str] = []

    for block in soup.select(".content-area"):
        heading = block.find("h2")
        body = block.find(class_="rte")
        parts = []
        if heading:
            parts.append(heading.get_text(" ", strip=True))
        if body:
            parts.append(body.get_text(" ", strip=True))
        combined = " ".join(p for p in parts if p)
        if combined:
            chunks.append(combined)

    for node in soup.select(".rte"):
        txt = node.get_text(" ", strip=True)
        if not txt or len(txt) <= 10:
            continue
        if txt not in chunks:
            chunks.append(txt)

    if chunks:
        return "\n".join(chunks)

    meta = soup.select_one("meta[property='og:description'], meta[name='description']")
    return meta.get("content", "").strip() if meta else ""


def _extract_bg_image_url(soup: BeautifulSoup) -> str | None:
    """Extract image URL from inline background-image (e.g., .bg-area)."""
    selectors = [
        ".bg-area[style]",
        ".product-image[style]",
        ".product-item[style]",
        "[style*='background-image']",
    ]
    candidates: list[str] = []
    for node in soup.select(", ".join(selectors)):
        style = node.get("style") or ""
        for m in re.finditer(r"background-image\s*:\s*url\(([^)]+)\)", style, re.IGNORECASE):
            val = m.group(1).strip(" '\"")
            if val:
                candidates.append(val)
    for attr in ("data-bgset", "data-bg", "data-background"):
        for node in soup.select(f"[{attr}]"):
            val = node.get(attr)
            if val:
                first = str(val).split(" ", 1)[0].strip()
                if first:
                    candidates.append(first)

    # Prefer product-specific paths.
    for kw in ("cdn.shopify.com", "/products/", "/files/"):
        for c in candidates:
            if kw in c:
                return c
    return candidates[0] if candidates else None


def _extract_ldjson_images(soup: BeautifulSoup) -> list[str]:
    images: list[str] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            types = item.get("@type")
            if types == "Product" or (isinstance(types, list) and "Product" in types):
                img = item.get("image")
                if isinstance(img, list):
                    images.extend([v for v in img if isinstance(v, str)])
                elif isinstance(img, str):
                    images.append(img)
    return images


def _select_image_url(soup: BeautifulSoup) -> str | None:
    """
    Collect image candidates and return the most product-specific:
    1) 背景圖（商品主圖常在此）
    2) LD+JSON image
    3) og/twitter image
    4) 第一張 img[src]
    """
    candidates: list[str] = []

    # 1) 背景圖優先
    bg = _normalize_image_url(_extract_bg_image_url(soup))
    if bg:
        candidates.append(bg)

    # 2) LD+JSON
    for u in _extract_ldjson_images(soup):
        norm = _normalize_image_url(u)
        if norm:
            candidates.append(norm)

    # 3) og/twitter
    meta = soup.select_one(
        "meta[property='og:image'], meta[name='og:image'], "
        "meta[name='twitter:image'], meta[property='twitter:image']"
    )
    if meta and meta.get("content"):
        norm = _normalize_image_url(meta.get("content", "").strip())
        if norm:
            candidates.append(norm)

    # 4) 第一張 <img src> / data-src 等
    for img in soup.select("img"):
        for attr in ("src", "data-src", "data-original", "data-lazy", "data-zoom-src"):
            val = img.get(attr)
            if not val:
                continue
            norm = _normalize_image_url(val)
            if norm:
                candidates.append(norm)

    # 改進評分:大幅提高正方形圖片的權重
    def score(url: str) -> int:
        s = 0
        lower = url.lower()
        
        # ★ 關鍵:用正則表達式判斷是否為正方形尺寸
        # 匹配模式如: _800x800. 或 _800x800_ 或 /800x800/
        if re.search(r'_(\d+)x\1[._/]', url) or re.search(r'/(\d+)x\1/', url):
            s += 50  # 大幅提高分數!
        
        # 原本的評分邏輯
        if lower.endswith(".jpg") or lower.endswith(".jpeg"):
            s += 6
        elif lower.endswith(".png"):
            s += 3
        if "/products/" in url:
            s += 5
        if "/files/" in url:
            s += 4
        
        # 降低寬圖、背景圖的分數
        if "banner" in lower:
            s -= 20
        if "bg" in lower or "background" in lower:
            s -= 10
        
        return s

    if not candidates:
        return None
    best = max(candidates, key=score)
    return best


def parse_product(html: str, url: str, category: str) -> Product:
    """Parse an AHC product page into a Product model."""
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.select_one("h2") or soup.select_one("h1")
    name = name_el.get_text(strip=True) if name_el else ""
    price = _extract_price(soup)

    description = _extract_description(soup)
    image_url = _select_image_url(soup)

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,
        description=description,
        url=_normalize_url(url),
        image_url=image_url,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )