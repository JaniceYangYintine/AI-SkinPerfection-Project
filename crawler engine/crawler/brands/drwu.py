"""Crawler for DR.WU products."""

from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "DR.WU"
BASE_URL = "https://www.drwu.com"

# Hard-coded category pages. Keep keys stable for downstream CSVs.
CATEGORY_PAGES: dict[str, str] = {
    "cleaner": "https://www.drwu.com/categories/clean",
    "toner": "https://www.drwu.com/categories/toner",
    "essence": "https://www.drwu.com/categories/essence",
    "eye-care": "https://www.drwu.com/categories/eye-care",
    "lotion-cream-gel": "https://www.drwu.com/categories/lotion-cream-gel",
    "key-repair": "https://www.drwu.com/categories/key-repair",
    "sunscreen": "https://www.drwu.com/categories/sunscreen",
}


def _normalize_url(url: str) -> str:
    """Drop query parameters to normalize product URLs."""
    return url.split("?", 1)[0]


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

            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            full_url = _normalize_url(full_url)

            key = (category, full_url)
            if key in seen:
                continue

            seen.add(key)
            results.append(key)

    return results


def parse_product(html: str, url: str, category: str) -> Product:
    """Parse a DR.WU product page into a Product model."""
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.select_one("h1")
    name = name_el.get_text(strip=True) if name_el else ""

    price_el = soup.select_one(".price, .product-price, span.price")
    price = price_el.get_text(strip=True) if price_el else None

    meta = soup.select_one("meta[property='og:description'], meta[name='description']")
    description = meta.get("content", "").strip() if meta else ""

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
