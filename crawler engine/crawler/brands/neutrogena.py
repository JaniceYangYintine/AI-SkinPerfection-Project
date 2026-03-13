"""Crawler for Neutrogena (neutrogena.com.tw)."""

import csv
from datetime import datetime
from typing import Any, Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BASE_URL = "https://www.neutrogena.com.tw"
LIST_URL = f"{BASE_URL}/products"
# In case the site paginates (e.g., 12 per page), also probe page 2/3.
LIST_URLS = [LIST_URL, f"{LIST_URL}?page=2", f"{LIST_URL}?page=3"]

BRAND = "Neutrogena"
# Specific selectors for 產品特色 / 使用方式 on product detail pages.
FEATURE_SELECTOR = "#產品特色 .rich-text"
USAGE_SELECTOR = "#使用方式 .rich-text"
# No real categories on-site; keep a single key for compatibility with Runner.
CATEGORY_PAGES: dict[str, str] = {f"all-{i}": url for i, url in enumerate(LIST_URLS, start=1)}

# Keywords to identify feature/usage sections (fallback when selectors change).
FEATURE_TITLES: tuple[str, ...] = ("產品特色", "商品特色")
USAGE_TITLES: tuple[str, ...] = ("使用方法", "使用", "使用說明")


def _normalize_url(url: str) -> str:
    """Drop query/anchors to keep product URLs stable."""
    return url.split("?", 1)[0].split("#", 1)[0]


def _clean_href(href: str) -> str:
    """Return absolute, normalized product URL or empty string if invalid."""
    full = href if href.startswith("http") else urljoin(BASE_URL, href)
    full = _normalize_url(full)
    if "/products/" not in full:
        return ""
    if full.rstrip("/").endswith("/products"):
        return ""
    return full


def _dedupe_pairs(pairs: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for cat, url in pairs:
        key = (cat, url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped


def get_product_urls(fetcher) -> list[str]:
    """Return all product URLs from the list page."""
    html = fetcher.get(LIST_URL)
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()

    for a in soup.select('a[href^="/products/"], a[href^="https://www.neutrogena.com.tw/products/"]'):
        href = a.get("href")
        if not href:
            continue
        full = _clean_href(href)
        if not full or full in seen:
            continue
        seen.add(full)
        urls.append(full)
    return urls


def get_product_urls_by_category(
    fetcher, category_pages: dict[str, str]
) -> list[tuple[str, str]]:
    """Return list of (category, product_url) pairs; Neutrogena has a single list page."""
    results: list[tuple[str, str]] = []

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select('a[href^="/products/"], a[href^="https://www.neutrogena.com.tw/products/"]'):
            href = a.get("href")
            if not href:
                continue
            full = _clean_href(href)
            if not full:
                continue
            results.append((category, full))

    return _dedupe_pairs(results)


def _collect_section_text(title_keywords: tuple[str, ...], soup: BeautifulSoup) -> str:
    """Grab text under the first h2 whose title contains any keyword (stop at next h2)."""
    for h2 in soup.select("h2"):
        title = h2.get_text(strip=True)
        if not any(key in title for key in title_keywords):
            continue
        chunks: list[str] = []
        node = h2.find_next_sibling()
        while node and getattr(node, "name", None) != "h2":
            text = node.get_text(" ", strip=True) if hasattr(node, "get_text") else ""
            if text:
                chunks.append(text)
            node = node.find_next_sibling()
        return " ".join(chunks).strip()
    return ""


def _get_text_by_selector(soup: BeautifulSoup, selector: str) -> str:
    """Return stripped text for the first matching element, or empty string."""
    el = soup.select_one(selector)
    return el.get_text(" ", strip=True) if el else ""


def _parse_product_dict(html: str, url: str, category: str) -> dict[str, Any]:
    """
    Parse a product page into a dict.

    Note: feature/usage 只用來組合進 description，同欄位輸出，避免額外欄位。
    """
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.select_one("h1")
    name = name_el.get_text(strip=True) if name_el else ""

    price_el = soup.select_one(".price, .product-price, span.price")
    price = price_el.get_text(strip=True) if price_el else ""

    meta = soup.select_one('meta[property="og:description"], meta[name="description"]')
    description = meta.get("content", "").strip() if meta else ""

    image_el = soup.select_one('meta[property="og:image"]')
    image_url = image_el.get("content", "").strip() if image_el else ""

    # Prefer explicit selectors; fall back to previous h2-based method if missing.
    feature = _get_text_by_selector(soup, FEATURE_SELECTOR)
    usage = _get_text_by_selector(soup, USAGE_SELECTOR)
    if not feature:
        feature = _collect_section_text(FEATURE_TITLES, soup)
    if not usage:
        usage = _collect_section_text(USAGE_TITLES, soup)

    merged_desc_parts = []
    if description:
        merged_desc_parts.append(str(description))
    if feature:
        merged_desc_parts.append(f"產品特色: {feature}")
    if usage:
        merged_desc_parts.append(f"使用方式: {usage}")

    return {
        "brand": BRAND,
        "category": category,
        "name": name,
        "price": price,
        "description": "\n".join(merged_desc_parts).strip(),
        "image_url": image_url,
        "url": _normalize_url(url),
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def parse_product(html: str, url: str, category: str) -> Product:
    """Parse a product page into the shared Product model，feature/usage 合併在 description。"""
    data = _parse_product_dict(html, url, category)

    product = Product(
        brand=BRAND,
        category=category,
        name=str(data.get("name", "")),
        price=data.get("price") or None,
        description=data.get("description", ""),
        url=_normalize_url(url),
        image_url=data.get("image_url"),
        crawled_at=data.get("crawled_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    return product
