"""Category-level scraper for Chanel: list product names/URLs from category pages."""

from datetime import datetime
from pathlib import Path
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "Chanel"
BASE_URL = "https://www.chanel.com"

# File with lines: category_label,category_url
CATEGORY_FILE = Path(__file__).resolve().parent.parent / "urls" / "chanel_categories.txt"


def _normalize_url(url: str) -> str:
    clean = url.split("?", 1)[0]
    return clean.split("#", 1)[0]


def _load_categories() -> List[tuple[str, str]]:
    """Load (label, category_url) pairs from config file."""
    if not CATEGORY_FILE.exists():
        print(f"[warn] category file not found: {CATEGORY_FILE}")
        return []
    entries: List[tuple[str, str]] = []
    for line in CATEGORY_FILE.read_text(encoding="utf-8-sig").splitlines():
        raw = line.strip().lstrip("\ufeff")
        if not raw:
            continue
        cat = "category"
        url = raw
        for sep in (",", "\t"):
            if sep in raw:
                parts = raw.split(sep, 1)
                if len(parts) == 2:
                    cat = parts[0].strip() or cat
                    url = parts[1].strip()
                break
        if url:
            entries.append((cat, url))
    return entries


def collect_category_items(fetcher) -> List[tuple[str, str, str]]:
    """Return list of (category_label, product_name, product_url) found in category pages."""
    entries = _load_categories()
    items: List[tuple[str, str, str]] = []
    for cat_label, cat_url in entries:
        try:
            html = fetcher.get(cat_url)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] fetch failed: {cat_url} ({exc})")
            continue
        soup = BeautifulSoup(html, "html.parser")
        seen: set[str] = set()
        for a in soup.select('a[href*="/p/"]'):
            href = a.get("href")
            if not href:
                continue
            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            full_url = _normalize_url(full_url)
            if full_url in seen:
                continue
            seen.add(full_url)
            name = a.get_text(" ", strip=True)
            items.append((cat_label, name, full_url))
    return items


def run(fetcher) -> List[Product]:
    items = collect_category_items(fetcher)
    products: List[Product] = []
    for cat_label, name, full_url in items:
        products.append(
            Product(
                brand=BRAND,
                category=cat_label,
                name=name,
                price=None,
                description="",
                url=full_url,
                crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
    return products
