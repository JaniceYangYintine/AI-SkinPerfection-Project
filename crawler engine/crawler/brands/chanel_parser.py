"""Crawler utilities for Chanel (Taiwan site)."""

import json
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "Chanel"
BASE_URL = "https://www.chanel.com"

# Use the all-skincare collection to enumerate products (when not manually provided).
CATEGORY_PAGES: dict[str, str] = {
    "skincare": f"{BASE_URL}/tw/skincare/c/beauty/skincare/all-skincare/",
}


def _normalize_url(url: str) -> str:
    """Normalize product URLs by dropping query/fragment."""
    clean = url.split("?", 1)[0]
    return clean.split("#", 1)[0]


def _normalize_price_value(raw: object) -> str | None:
    """Ensure price like 'NT$ 3,800' or '3800' -> 'NT$3,800'."""
    if raw is None:
        return None
    text = str(raw).strip()
    m = re.search(r"([\d,]+(?:\.\d+)?)", text.replace("NT$", ""))
    if not m:
        return None
    number = m.group(1)
    return f"NT${number}"


def get_product_urls_by_category(
    fetcher, category_pages: dict[str, str]
) -> list[tuple[str, str]]:
    """Return list of (category, product_url) pairs discovered on category pages."""
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select('a[href*="/p/"]'):
            href = a.get("href")
            if not href:
                continue
            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            full_url = _normalize_url(full_url)
            if full_url in seen:
                continue
            seen.add(full_url)
            results.append((category, full_url))

    return results


def _extract_price(soup: BeautifulSoup) -> str | None:
    """Parse price from JSON-LD offers or visible price block."""
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
                    price = offers.get("price") or offers.get("priceAmount")
                    normalized = _normalize_price_value(price)
                    if normalized:
                        return normalized

    price_node = soup.select_one('[data-test="price-value"], .product-price, .price')
    if price_node:
        txt = price_node.get_text(" ", strip=True)
        normalized = _normalize_price_value(txt)
        if normalized:
            return normalized

    meta_price = soup.select_one(
        "meta[property='product:price:amount'], meta[property='og:price:amount']"
    )
    if meta_price and meta_price.get("content"):
        normalized = _normalize_price_value(meta_price["content"])
        if normalized:
            return normalized

    return None


def _extract_description(soup: BeautifulSoup) -> str:
    """Prefer main description block; fallback to meta description."""
    desc_node = soup.select_one(
        "[data-test='pdp-description'], .product-description, .rich-text, .rte"
    )
    if desc_node:
        text = desc_node.get_text(" ", strip=True)
        if text:
            return text

    meta = soup.select_one("meta[property='og:description'], meta[name='description']")
    if meta and meta.get("content"):
        return meta["content"].strip()

    return ""


def _extract_sections_from_text(full_text: str) -> dict[str, str]:
    """
    Extract sections like 產品說明 / 產品功效 / 活性成分 / 使用程序 from a full page text blob.
    """
    if not full_text:
        return {}
    markers = [
        ("產品說明", "description"),
        ("產品功效", "benefit"),
        ("活性成分", "ingredients"),
        ("使用程序", "usage"),
        ("使用方法", "usage"),
        ("使用說明", "usage"),
    ]
    positions: list[tuple[int, str, str]] = []
    for kw, label in markers:
        pos = full_text.find(kw)
        if pos != -1:
            positions.append((pos, kw, label))
    if not positions:
        return {}
    positions.sort(key=lambda x: x[0])

    stop_tokens = [
        "返回詳情",
        "更多資訊",
        "尺寸",
        "成分清單",
        "評論",
        "其他產品",
        "重點保養程序",
        "香奈兒首頁",
        "包裝的藝術",
        "配送及退貨",
    ]

    def _trim_at_stop(snippet: str) -> str:
        cut_positions = [snippet.find(tok) for tok in stop_tokens if tok in snippet]
        cut_positions = [p for p in cut_positions if p >= 0]
        if cut_positions:
            cut_at = min(cut_positions)
            return snippet[:cut_at].strip()
        return snippet.strip()

    sections: dict[str, str] = {}
    for idx, (pos, kw, label) in enumerate(positions):
        start = pos + len(kw)
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(full_text)
        raw = full_text[start:end]
        snippet = _trim_at_stop(raw)
        if snippet:
            sections[label] = snippet
    return sections


def _infer_category_from_url(url: str, fallback: str) -> str:
    """
    Try to derive category from URL path, e.g. /tw/skincare/p/... -> skincare.
    """
    if fallback and fallback not in ("", "manual"):
        return fallback
    path = url.split("://", 1)[-1]
    parts = [p for p in path.split("/") if p]
    for p in parts:
        if p.lower() in ("skincare", "makeup", "fragrance", "beauty"):
            return p.lower()
    return fallback


def parse_product(html: str, url: str, category: str) -> Product:
    """Parse a Chanel product page into a Product model."""
    soup = BeautifulSoup(html, "html.parser")

    name_node = soup.select_one("h1") or soup.select_one("[data-test='pdp-title']")
    if not name_node:
        name_node = soup.select_one("meta[property='og:title']")
    name = (
        name_node.get_text(strip=True)
        if name_node and hasattr(name_node, "get_text")
        else name_node.get("content", "").strip()
        if name_node
        else ""
    )

    price = _extract_price(soup)
    description = _extract_description(soup)
    category = _infer_category_from_url(url, category)
    image_url = None
    meta_img = soup.select_one(
        "meta[property='og:image'], meta[name='og:image'], "
        "meta[name='twitter:image'], meta[property='twitter:image']"
    )
    if meta_img and meta_img.get("content"):
        image_url = meta_img["content"].strip()
    if not image_url:
        img = soup.select_one("img[src]")
        if img and img.get("src"):
            image_url = img["src"].strip()

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


def parse_product_with_text(
    html: str, full_text: str, url: str, category: str
) -> Product:
    """Parse product and enrich description using full page text (e.g. soup.get_text or Playwright inner_text)."""
    product = parse_product(html, url, category)
    sections = _extract_sections_from_text(full_text)
    combined_parts: list[str] = []
    labels = {
        "description": "產品說明",
        "benefit": "產品功效",
        "ingredients": "活性成分",
        "usage": "使用說明",
    }
    for key in ("description", "benefit", "ingredients", "usage"):
        if key in sections:
            combined_parts.append(f"{labels.get(key, key)}：{sections[key]}")
    if combined_parts:
        product.description = "\n".join(combined_parts)
    return product
