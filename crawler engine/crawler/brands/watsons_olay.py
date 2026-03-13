"""Crawler for Olay products listed on Watsons Taiwan."""

from __future__ import annotations

import json
import re
import html
from datetime import datetime
import random
import time
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "Olay (Watsons TW)"
BASE_URL = "https://www.watsons.com.tw"

# Watsons brand landing page; pagination is handled in get_product_urls_by_category.
CATEGORY_PAGES: dict[str, str] = {
    "all": "https://www.watsons.com.tw/all-brands/list/166024/olay?q=:bestSeller:productBrandCode:166024"
}

# Guard rails to avoid infinite pagination loops.
MAX_PAGES_PER_CATEGORY = 15

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

# Headings that usually precede the product description block on Watsons.
DESC_KEYWORDS = (
    "詳細介紹",
    "詳情介紹",
    "商品描述",
    "商品介紹",
    "商品詳情",
    "商品資訊",
    "商品信息",
    "商品特色",
    "產品介紹",
    "產品詳情",
    "產品資訊",
)


def _normalize_url(url: str) -> str:
    """Ensure absolute URL and strip query/fragment."""
    full = urljoin(BASE_URL, url)
    parsed = urlparse(full)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _page_url(base: str, page: int) -> str:
    if page == 0:
        return base
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}page={page}"


def _extract_links_from_soup(soup: BeautifulSoup) -> list[str]:
    """Collect product detail links present in the rendered HTML."""
    links: list[str] = []
    for a in soup.select('a[href]'):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if "/p/" in href or "ProductDisplay" in href:
            links.append(href)
    # Deduplicate while preserving order.
    seen: set[str] = set()
    uniq: list[str] = []
    for href in links:
        if href in seen:
            continue
        seen.add(href)
        uniq.append(href)
    return uniq


def _extract_links_from_text(html: str) -> list[str]:
    """
    Some product tiles are rendered via client-side JS but URLs still appear in JSON blobs.
    Try to pull them with regex to avoid missing items.
    """
    pattern = re.compile(r"https?://www\.watsons\.com\.tw[^\"'\\s]+/p/[A-Z0-9_]+", re.IGNORECASE)
    urls = pattern.findall(html)

    rel_pattern = re.compile(r'"(/[^\"\\s]+/p/[A-Z0-9_]+)"')
    urls.extend(rel_pattern.findall(html))

    # Normalize and dedupe.
    seen: set[str] = set()
    uniq: list[str] = []
    for href in urls:
        full = _normalize_url(href)
        if full in seen:
            continue
        seen.add(full)
        uniq.append(full)
    return uniq


def _get_html(fetcher, url: str, *, timeout: int = 30, retries: int = 2) -> str:
    """
    Brand-specific fetch with longer timeout/retries; keeps other brands untouched.
    """
    last_exc: Exception | None = None
    delay_range = getattr(fetcher, "delay_range", (0.8, 1.8))

    for attempt in range(retries + 1):
        if attempt:
            time.sleep(1.2 * attempt)
        try:
            time.sleep(random.uniform(*delay_range))
            resp = fetcher.session.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except Exception as exc:  # noqa: BLE001 - log at caller
            last_exc = exc
            continue
    raise last_exc or Exception("unknown fetch error")


def get_product_urls_by_category(fetcher, category_pages: dict[str, str]) -> list[tuple[str, str]]:
    """
    Return (category, product_url) pairs discovered from the brand landing page.
    Pagination is handled by appending ?page=N until no new products are found or the max cap is hit.
    """
    results: list[tuple[str, str]] = []

    for category, base_url in category_pages.items():
        seen: set[str] = set()
        page = 0

        while page < MAX_PAGES_PER_CATEGORY:
            page_url = _page_url(base_url, page)
            html = _get_html(fetcher, page_url)
            soup = BeautifulSoup(html, "html.parser")

            links = _extract_links_from_soup(soup)
            links.extend(_extract_links_from_text(html))

            new_count = 0
            for href in links:
                full = _normalize_url(href)
                key = (category, full)
                if key in seen:
                    continue
                seen.add(key)
                new_count += 1
                results.append(key)

            if new_count == 0:
                break

            page += 1

    return results


def _parse_jsonld_product(soup: BeautifulSoup) -> dict[str, Any]:
    """Return the first JSON-LD Product object, if present."""
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


def _decode_jsonld_description(desc_raw: str) -> str:
    """
    Decode Watsons JSON-LD description which often embeds escaped HTML like \\u003Cdiv class="longDesc"\\u003E...
    """
    if not desc_raw:
        return ""

    # If原字串已是正常中文，不要再解碼以免亂碼。
    if "\\u003" not in desc_raw and "\\u00" not in desc_raw and "&lt;" not in desc_raw:
        return desc_raw.strip()

    # Replace common escapes first.
    text = (
        desc_raw.replace("\\u003C", "<")
        .replace("\\u003E", ">")
        .replace("\\u0026", "&")
    )
    text = html.unescape(text)

    # Best-effort unicode escape decode (e.g., \u003Cdiv...).
    try:
        text = text.encode().decode("unicode_escape")
    except Exception:
        pass

    desc_soup = BeautifulSoup(text, "html.parser")

    long_desc = desc_soup.select_one("div.longDesc")
    if long_desc:
        for iframe in long_desc.select("iframe"):
            iframe.decompose()
        content = long_desc.get_text("\n", strip=True)
        if content:
            return content

    fallback = desc_soup.get_text("\n", strip=True)
    return fallback

def _extract_category(soup: BeautifulSoup, product_name: str = "") -> str:
    """
    Category comes from breadcrumb span: <span itemprop="name" class="ng-star-inserted">精華液 /霜</span>
    Pick the last breadcrumb that is not the product name itself.
    """
    crumbs: list[str] = []
    for span in soup.select('nav.breadcrumb span[itemprop="name"], ol.breadcrumb span[itemprop="name"], span[itemprop="name"].ng-star-inserted'):
        text = span.get_text(strip=True)
        if text:
            crumbs.append(text)

    # Heuristic: last crumb is often the product name; pick the previous one.
    for text in reversed(crumbs):
        if text and text != product_name:
            return text
    return ""

def _extract_description(soup: BeautifulSoup, jsonld: dict[str, Any]) -> str:
    desc = (jsonld.get("description") or "").strip() if jsonld else ""
    decoded = _decode_jsonld_description(desc)

    # Watsons product detail block: <p class="ecTitle">詳細介紹</p> followed by <div class="longDesc">...</div>
    for heading in soup.select("p.ecTitle"):
        title_text = heading.get_text(strip=True)
        if not title_text or any(k in title_text for k in DESC_KEYWORDS):
            long_desc = heading.find_next_sibling("div", class_="longDesc")
            if long_desc:
                text = long_desc.get_text("\n", strip=True)
                if text:
                    return text

    # Standalone longDesc, if any.
    long_desc = soup.select_one("div.longDesc")
    if long_desc:
        text = long_desc.get_text("\n", strip=True)
        if text:
            return text

    detail_blocks = soup.select(
        ".product-details-container, .product-details, #productDetail, "
        "#product-details, [id*='detail'], [data-qa='product-details']"
    )
    for block in detail_blocks:
        text = block.get_text("\n", strip=True)
        if text:
            return text

    for heading in soup.select("h2, h3"):
        title_text = heading.get_text(strip=True)
        if any(k in title_text for k in DESC_KEYWORDS):
            parts: list[str] = []
            node = heading.find_next_sibling()
            while node and getattr(node, "name", None) not in ("h2", "h3"):
                text = node.get_text(" ", strip=True) if hasattr(node, "get_text") else ""
                if text:
                    parts.append(text)
                node = node.find_next_sibling()
            if parts:
                return "\n".join(parts).strip()

    # If nothing from DOM, fall back to decoded JSON-LD (may contain HTML text).
    if decoded:
        return decoded

    if desc:
        return desc

    # Fallback to meta description.
    meta_desc = soup.select_one(
        'meta[name="description"], meta[property="og:description"], meta[name="og:description"]'
    )
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"].strip()

    return ""


def _extract_price(soup: BeautifulSoup, jsonld: dict[str, Any]) -> str | None:
    offers = jsonld.get("offers") if isinstance(jsonld, dict) else None
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice") or offers.get("highPrice")
        if price:
            return str(price).strip()

    meta = soup.select_one('meta[property="product:price:amount"]')
    if meta and meta.get("content"):
        return meta["content"].strip()

    price_el = soup.select_one('[itemprop="price"], .price, .product-price')
    if price_el:
        if price_el.has_attr("content"):
            return price_el["content"].strip()
        text = price_el.get_text(strip=True)
        if text:
            return text
    return None


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    jsonld = _parse_jsonld_product(soup)

    name = (jsonld.get("name") or "").strip() if jsonld else ""
    if not name:
        h1 = soup.select_one("h1, h1[itemprop='name']")
        name = h1.get_text(strip=True) if h1 else ""

    cat_from_page = _extract_category(soup, name)

    description = _extract_description(soup, jsonld)
    price = _extract_price(soup, jsonld)
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
        category=cat_from_page or category,
        name=name,
        price=price,
        description=description,
        url=_normalize_url(url),
        image_url=image_url,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    return product


def run(fetcher, limit: int | None = None) -> list[Product]:
    """
    Brand-specific runner to use longer timeout/retries without affecting other brands.
    """
    pairs = get_product_urls_by_category(fetcher, CATEGORY_PAGES)
    if limit is not None:
        pairs = pairs[:limit]
    products: list[Product] = []

    for category, url in pairs:
        try:
            html = _get_html(fetcher, url)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] fetch failed: {url} ({exc})")
            continue

        try:
            product = parse_product(html, url, category)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] parse failed: {url} ({exc})")
            continue

        if product and getattr(product, "name", None):
            products.append(product)
        else:
            print(f"[warn] skipped empty product: {url}")

    return products
