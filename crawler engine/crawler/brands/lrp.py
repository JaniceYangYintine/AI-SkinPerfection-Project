"""Crawler for La Roche-Posay (lrp.com.tw)."""

import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "La Roche-Posay"
BASE_URL = "https://www.lrp.com.tw"

# Hard-coded category pages. Keys are human-readable tags for output.
CATEGORY_PAGES: dict[str, str] = {
    "cleanser": f"{BASE_URL}/Product/List/Index/CLEANSER?MenuType=ProductType",
    "lotion": f"{BASE_URL}/Product/List/Index/LOTION?MenuType=ProductType",
    "essence": f"{BASE_URL}/Product/List/Index/ESSENCE?MenuType=ProductType",
    "fluide": f"{BASE_URL}/Product/List/Index/FLUIDE?MenuType=ProductType",
    "cream": f"{BASE_URL}/Product/List/Index/CREAM?MenuType=ProductType",
    "suncare": f"{BASE_URL}/Product/List/Index/SUNCARE?MenuType=ProductType",
    "suncare-makeup": f"{BASE_URL}/Product/List/Index/SUNCARE_MAKEUP?MenuType=ProductType",
    "treatment": f"{BASE_URL}/Product/List/Index/TREATMENT?MenuType=ProductType",
    "eyecare": f"{BASE_URL}/Product/List/Index/EYECARE?MenuType=ProductType",
}


def _normalize_url(url: str) -> str:
    """Keep strProductID, drop other query/anchors to normalize URLs."""
    if "strProductID=" in url:
        base, _, qs = url.partition("?")
        match = re.search(r"(strProductID=[^&]+)", qs)
        return f"{base}?{match.group(1)}" if match else url
    return url.split("#", 1)[0]


def get_product_urls_by_category(
    fetcher, category_pages: dict[str, str]
) -> list[tuple[str, str]]:
    """Return list of (category, product_url) pairs discovered on category pages."""
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select('a[href*="/Product/Content"]'):
            href = a.get("href")
            if not href or "strProductID=" not in href:
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
    """Extract NT$ price with multiple selector/regex fallbacks."""
    cand = soup.select_one(
        ".price, .product-price, .productPrice, .ProductPrice, span.price, .price-area"
    )
    if cand:
        txt = cand.get_text(" ", strip=True)
        match = re.search(r"NT\$\s*[\d,]+", txt)
        if match:
            return match.group(0).replace(" ", "")

    text = soup.get_text("\n", strip=True)
    match = re.search(r"NT\$\s*([\d,]+)", text)
    if match:
        digits = match.group(1)
        return f"NT${digits.replace(',', '')}" if "," not in digits else f"NT${digits}"

    return None


def _extract_description(soup: BeautifulSoup) -> str:
    """Prefer meta description; fallback to intro section under h2 titles."""
    meta = soup.select_one("meta[property='og:description'], meta[name='description']")
    if meta and meta.get("content"):
        return meta["content"].strip()

    for h2 in soup.select("h2"):
        title = h2.get_text(strip=True)
        if "介" in title or "紹" in title:
            chunks: list[str] = []
            node = h2.find_next_sibling()
            while node and getattr(node, "name", None) != "h2":
                text = node.get_text(" ", strip=True) if hasattr(node, "get_text") else ""
                if text:
                    chunks.append(text)
                node = node.find_next_sibling()
            desc = " ".join(chunks).strip()
            if desc:
                return desc

    return ""


def parse_product(html: str, url: str, category: str) -> Product:
    """Parse a La Roche-Posay product page into a Product model."""
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.select_one("h1")
    name = name_el.get_text(strip=True) if name_el else ""

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