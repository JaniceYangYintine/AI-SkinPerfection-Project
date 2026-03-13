"""Crawler for Shu Uemura (Taiwan site)."""

import json
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "Shu Uemura"
BASE_URL = "https://www.shuuemura.com.tw"

# Focus on skincare-related categories.
CATEGORY_PAGES: dict[str, str] = {
    "cleanser": f"{BASE_URL}/categories/%E6%BD%94%E9%A1%8F%E6%85%95%E6%96%AF",
    "toner": f"{BASE_URL}/categories/%E5%8C%96%E5%A6%9D%E6%B0%B4",
    "serum": f"{BASE_URL}/categories/%E7%B2%BE%E8%8F%AF%E6%B6%B2",
    "lotion": f"{BASE_URL}/categories/%E4%B9%B3%E6%B6%B2",
    "cream": f"{BASE_URL}/categories/%E4%B9%B3%E9%9C%9C",
}

def _normalize_url(url: str) -> str:
    """Drop query/fragment for stable product URLs."""
    clean = url.split("?", 1)[0]
    return clean.split("#", 1)[0]


def _format_price_value(value: object) -> str:
    """Format numeric price values without trailing .0."""
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value))
        return str(value)
    return str(value)


def _iter_ldjson_products(soup: BeautifulSoup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Product":
                yield item


def get_product_urls_by_category(
    fetcher, category_pages: dict[str, str]
) -> list[tuple[str, str]]:
    """Return list of (category, product_url) pairs discovered on category pages."""
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select('a[href*="/products/"]'):
            href = a.get("href")
            if not href:
                continue
            if href.rstrip("/").endswith("/products"):
                continue
            if href.startswith("http") and not href.startswith(BASE_URL):
                continue

            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            full_url = _normalize_url(full_url)

            key = (category, full_url)
            if key in seen:
                continue
            seen.add(key)
            results.append(key)

    return results


def _extract_price(soup: BeautifulSoup) -> str | None:
    """Prefer LD+JSON offers; fallback to visible price/meta tags."""
    for item in _iter_ldjson_products(soup):
        offers = item.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else None
        if isinstance(offers, dict):
            price_val = offers.get("price") or offers.get("priceAmount")
            currency = offers.get("priceCurrency") or "TWD"
            if price_val is not None:
                prefix = "NT$" if currency in ("TWD", "NTD") else f"{currency} "
                return f"{prefix}{_format_price_value(price_val)}"

    price_el = soup.select_one(".product-price, .price")
    if price_el:
        text = price_el.get_text(" ", strip=True)
        if text:
            return text

    meta_price = soup.select_one(
        "meta[property='product:price:amount'], meta[property='og:price:amount']"
    )
    if meta_price and meta_price.get("content"):
        return f"NT${meta_price['content']}"

    return None


def _extract_description(soup: BeautifulSoup) -> str:
    """Pull LD+JSON description, then meta description, then page content."""
    for item in _iter_ldjson_products(soup):
        desc = item.get("description")
        if isinstance(desc, str):
            cleaned = desc.replace("\xa0", " ").strip()
            if cleaned:
                return cleaned

    meta = soup.select_one("meta[property='og:description'], meta[name='description']")
    if meta and meta.get("content"):
        return meta["content"].strip()

    content = soup.select_one(".product-description, .product-short-description")
    if content:
        txt = content.get_text(" ", strip=True)
        if txt:
            return txt

    return ""


def parse_product(html: str, url: str, category: str) -> Product:
    """Parse a Shu Uemura product page into a Product model."""
    soup = BeautifulSoup(html, "html.parser")

    name_node = soup.select_one("h1") or soup.select_one("meta[property='og:title']")
    name = (
        name_node.get_text(strip=True)
        if name_node and hasattr(name_node, "get_text")
        else name_node.get("content", "").strip()
        if name_node
        else ""
    )

    price = _extract_price(soup)
    description = _extract_description(soup)

    image_el = soup.select_one("meta[property='og:image']")
    image_url = image_el.get("content", "").strip() if image_el else None

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
