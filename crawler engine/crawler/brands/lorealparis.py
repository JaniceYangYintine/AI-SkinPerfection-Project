"""Crawler for L'Oreal Paris Taiwan (lorealparis.com.tw)."""

from datetime import datetime
from html import unescape
import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "Loreal Paris"
DOMAIN = "https://www.lorealparis.com.tw"

# Map provided category URLs to human-friendly labels.
CATEGORY_PAGES: dict[str, str] = {
    "化妝水/精華水": f"{DOMAIN}/face-care/water-essence",
    "清潔/卸妝": f"{DOMAIN}/face-care/facial-treatment",
    "精華液": f"{DOMAIN}/face-care/face-serum",
    "乳液/面霜": f"{DOMAIN}/face-care/lotion-and-cream",
    "眼霜/眼部精華": f"{DOMAIN}/face-care/eye-cream",
    "防曬/妝前": f"{DOMAIN}/face-care/uv-city-resist",
}

# Cache prices found on listing pages, keyed by normalized product URL.
PRICE_CACHE: dict[str, str] = {}


def _normalize_url(url: str) -> str:
    """Strip query/fragment and ensure absolute."""
    full = urljoin(DOMAIN, url)
    parsed = urlparse(full)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _extract_product_urls_from_html(html: str) -> list[tuple[str, str | None]]:
    """
    Product list is embedded in JSON-ish blobs containing URL and price, e.g.:
    "url":"/glycolic-bright/glc-br-peeling-water","buyNowUrl":null,"position":1,
    "itemResult":{"type":"Product",...,"price":"NT$ 939","priceNumber":"939",...}
    """
    unescaped = unescape(html)
    pattern = re.compile(
        r'"url":"(?P<url>/[^"]+?)","buyNowUrl":null,"position":\d+,'
        r'"itemResult":\{"type":"Product".+?"priceNumber":"(?P<price>[^"]+)"',
        re.DOTALL,
    )
    items: list[tuple[str, str | None]] = []
    for match in pattern.finditer(unescaped):
        items.append((match.group("url"), match.group("price")))
    return items


def get_product_urls_by_category(fetcher, category_pages: dict[str, str]) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        for rel_url, price in _extract_product_urls_from_html(html):
            full = _normalize_url(rel_url)
            if price:
                PRICE_CACHE[full] = price.strip()
            key = (category, full)
            if key in seen:
                continue
            seen.add(key)
            results.append(key)

    return results


def _parse_jsonld_product(soup: BeautifulSoup) -> dict[str, Any]:
    """Return the first JSON-LD Product object, if any."""
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
            types = obj.get("@type")
            if types == "Product" or (isinstance(types, list) and "Product" in types):
                return obj
    return {}


def _extract_description(soup: BeautifulSoup, jsonld: dict[str, Any]) -> str:
    # Prefer JSON-LD description.
    desc = (jsonld.get("description") or "").strip() if jsonld else ""
    if desc:
        return desc

    # Try the "產品介紹" collapsible block.
    for details in soup.select("details"):
        summary = details.find("summary")
        if summary and "產品介紹" in summary.get_text(strip=True):
            text = details.get_text("\n", strip=True)
            if text:
                return text

    # Fallback to meta description.
    meta = soup.select_one('meta[property="og:description"], meta[name="description"]')
    return meta.get("content", "").strip() if meta and meta.get("content") else ""


def _extract_price(soup: BeautifulSoup, jsonld: dict[str, Any]) -> str | None:
    offers = jsonld.get("offers") if isinstance(jsonld, dict) else None
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice") or offers.get("highPrice")
        if price:
            return str(price).strip()

    meta_price = soup.select_one('meta[property="product:price:amount"]')
    if meta_price and meta_price.get("content"):
        return meta_price["content"].strip()

    price_el = soup.select_one('[data-product-price], .product-price, [itemprop="price"]')
    if price_el:
        if price_el.has_attr("content"):
            return price_el["content"].strip()
        txt = price_el.get_text(strip=True)
        if txt:
            return txt
    return None


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    jsonld = _parse_jsonld_product(soup)

    name = (jsonld.get("name") or "").strip() if jsonld else ""
    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""

    description = _extract_description(soup, jsonld)
    price = _extract_price(soup, jsonld)
    if not price:
        cached_price = PRICE_CACHE.get(_normalize_url(url))
        if cached_price:
            price = cached_price
    image_url = None
    if isinstance(jsonld, dict):
        img = jsonld.get("image")
        if isinstance(img, list) and img:
            img = img[0]
        if isinstance(img, str):
            image_url = img.strip()
    if not image_url:
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

    product = Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,
        description=description,
        url=_normalize_url(url),
        image_url=image_url,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    return product
