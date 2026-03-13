# brands/kiehls.py
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crawler.engine.models import Product

BRAND = "KIEHLS"
DOMAIN = "https://www.kiehls.com.tw"

CATEGORY_PAGES = {
    "臉部清潔": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E6%B8%85%E6%BD%94%E5%8D%B8%E5%A6%9D",
    "化妝水": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E5%8C%96%E5%A6%9D%E6%B0%B4",
    "精華液": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E7%B2%BE%E8%8F%AF%E6%B6%B2",
    "乳液/乳霜": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E4%B9%B3%E6%B6%B2%2C%E4%B9%B3%E9%9C%9C%2C%E5%87%9D%E5%87%8D",
    "保濕棒": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E4%BF%9D%E6%BF%95%E6%A3%92",
    "面膜": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E9%9D%A2%E8%86%9C",
    "隔離防曬": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E9%9A%94%E9%9B%A2%E9%98%B2%E6%9B%AC",
    "眼唇護理": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E7%9C%BC%E5%94%87%E8%AD%B7%E7%90%86",
    "液態痘痘貼": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E6%B6%B2%E6%85%8B%E7%97%98%E7%97%98%E8%B2%BC",
    "酸類煥膚": "https://www.kiehls.com.tw/category/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81/%E9%85%B8%E9%A1%9E%E7%85%A5%E8%86%9A",
}

# Kiehl's (SFCC/Demandware) 產品卡片懶載入 API（你抓到的那條）
CDS_TILE_ENDPOINT = (
    "https://www.kiehls.com.tw/on/demandware.store/"
    "Sites-kiehls-tw-ng-Site/zh_TW/"
    "CDSLazyload-product_productmainaction"
)

# 盡量像正常瀏覽器，降低被擋機率（如果你的 fetcher.get 支援 headers，會自動帶上）
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.kiehls.com.tw/",
}

# 從分類頁抓 pid：data-pid="..." 或 pid&quot;:&quot;...&quot;
_PID_RE = re.compile(r'data-pid="(\d{13})"|pid&quot;:&quot;(\d{13})&quot;')


def _normalize_url(url: str) -> str:
    """移除 query 與 fragment，避免重複"""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _fetch(fetcher, url: str) -> str:
    """
    相容不同 fetcher.get() 簽名：
    - 若支援 headers 參數 → 帶 DEFAULT_HEADERS
    - 否則用原本 fetcher.get(url)
    """
    try:
        return fetcher.get(url, headers=DEFAULT_HEADERS)  # type: ignore[arg-type]
    except TypeError:
        return fetcher.get(url)


def _extract_pids_from_category_html(html: str) -> list[str]:
    pids: set[str] = set()
    for m in _PID_RE.finditer(html):
        pid = m.group(1) or m.group(2)
        if pid:
            pids.add(pid)
    return list(pids)


def _build_tile_url(pid: str) -> str:
    # 直接用你提供的 query（includePrice=false 也OK，先拿到商品 URL 最重要）
    return (
        f"{CDS_TILE_ENDPOINT}"
        f"?configExtension=%7b%22includePrice%22%3afalse%2c%22isPriceBelowText%22%3afalse%7d"
        f"&configid=producttile"
        f"&data={pid}"
        f"&id=productmainaction"
        f"&pageId=producttile"
        f"&section=product"
        f"&ajax=true"
    )


def _extract_product_url_from_tile_response(tile_resp: str) -> str | None:
    """
    CDSLazyload 回來通常是 HTML 片段（product tile）
    我們從裡面找商品頁連結。
    """
    soup = BeautifulSoup(tile_resp, "html.parser")

    # 優先找最像商品頁的 a[href]
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        # 先放寬：只要 href 裡看起來像商品頁就收
        if "/product" in href or "/products" in href:
            return href

    # 若 HTML 解析不到，退而求其次：用 regex 直接撈 href
    m = re.search(r'href="([^"]+)"', tile_resp)
    if m:
        href = m.group(1).strip()
        if ("/product" in href) or ("/products" in href):
            return href

    return None


def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    """
    回傳：(category_key, product_url)
    Kiehl's 分類頁是 JS + lazyload：
    1) 先從分類頁 HTML 抓 pid
    2) 對每個 pid 打 CDSLazyload API 拿 tile HTML
    3) 從 tile HTML 抽商品 URL
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        cat_html = _fetch(fetcher, page_url)

        pids = _extract_pids_from_category_html(cat_html)
        if not pids:
            # 有些分類頁可能需要滾動才會出現更多 pid；至少先把能抓到的抓完
            continue

        for pid in pids:
            tile_url = _build_tile_url(pid)
            tile_resp = _fetch(fetcher, tile_url)

            href = _extract_product_url_from_tile_response(tile_resp)
            if not href:
                continue

            full_url = href if href.startswith("http") else urljoin(DOMAIN, href)
            full_url = _normalize_url(full_url)

            key = (category, full_url)
            if key in seen:
                continue

            seen.add(key)
            results.append((category, full_url))

    return results


def _parse_jsonld_product(soup: BeautifulSoup) -> dict[str, Any]:
    """嘗試從 JSON-LD 抓商品資料（最穩）"""
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
            if t == "Product" or (isinstance(t, list) and "Product" in t):
                return obj
    return {}


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")

    # 先用 JSON-LD
    j = _parse_jsonld_product(soup)

    name = (j.get("name") or "").strip()
    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""

    price = None
    offers = j.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
        if price is not None:
            price = str(price).strip()

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
