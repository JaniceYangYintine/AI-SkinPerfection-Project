"""Crawler for Chanel skincare (chanel.com/tw)."""

from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "Chanel"

CATEGORY_PAGES: dict[str, str] = {
    "化妝水/前導": "https://www.chanel.com/tw/skincare/toners-lotions/c/6x1x9/",
    "精華": "https://www.chanel.com/tw/skincare/serums/c/6x1x3/",
    "乳霜/乳液": "https://www.chanel.com/tw/skincare/moisturizers/c/6x1x5/",
    "油類": "https://www.chanel.com/tw/skincare/oils/c/6x1x8/",
    "防曬": "https://www.chanel.com/tw/skincare/sun-protection/c/6x1x6/",
}

# Product cards typically link to /tw/skincare/p/<slug>/ ; keep both absolute and relative.
PRODUCT_LINK_SELECTOR = 'a[href*="/skincare/p/"], a[href^="/tw/skincare/p/"]'


def _normalize_url(url: str) -> str:
    return url.split("?", 1)[0].split("#", 1)[0]


def get_product_urls_by_category(fetcher, category_pages: dict[str, str]) -> list[tuple[str, str]]:
    """Return list of (category, product_url) pairs across the five entry pages."""
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select(PRODUCT_LINK_SELECTOR):
            href = a.get("href") or ""
            full = urljoin(page_url, href)
            full = _normalize_url(full)
            if "/skincare/p/" not in full:
                continue
            key = (category, full)
            if key in seen:
                continue
            seen.add(key)
            results.append(key)

    return results


def _extract_meta_description(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[property="og:description"], meta[name="description"]')
    return meta.get("content", "").strip() if meta and meta.get("content") else ""


def _extract_price(soup: BeautifulSoup) -> str:
    # Chanel often shows price in meta or data-price attributes.
    price_el = soup.select_one('[data-product-price], .product-price, [itemprop="price"]')
    if price_el:
        if price_el.has_attr("content"):
            return price_el["content"].strip()
        if price_el.get_text(strip=True):
            return price_el.get_text(strip=True)
    meta_price = soup.select_one('meta[property="product:price:amount"]')
    if meta_price and meta_price.get("content"):
        return meta_price["content"].strip()
    return ""


def _extract_effect(soup: BeautifulSoup) -> str:
    # Look for “功效” block under product details; fallback to None.
    for h2 in soup.select("h2, h3"):
        title = h2.get_text(strip=True)
        if "功效" in title:
            parts: list[str] = []
            node = h2.find_next_sibling()
            while node and getattr(node, "name", None) not in ("h2", "h3"):
                text = node.get_text(" ", strip=True) if hasattr(node, "get_text") else ""
                if text:
                    parts.append(text)
                node = node.find_next_sibling()
            return " ".join(parts).strip()
    return ""


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.select_one("h1, h1[itemprop='name']")
    name = name_el.get_text(strip=True) if name_el else ""

    price = _extract_price(soup)
    description = _extract_meta_description(soup)

    effect = _extract_effect(soup) or None  # None when missing

    product = Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price or None,
        description=description,
        url=_normalize_url(url),
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Attach custom field for brand-specific CSV if needed.
    product.effect = effect
    return product
