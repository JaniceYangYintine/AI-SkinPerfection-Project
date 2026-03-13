"""Shared runner for manual URL-based crawlers."""

from pathlib import Path
from typing import List

from bs4 import BeautifulSoup

from engine.models import Product
from engine.images import extract_image_url


def run_manual(fetcher, brand_module) -> List[Product]:
    """
    Generic manual runner:
    - expects brand_module.URL_LIST (Path) and brand_module.parse_product_with_text
    - fetches each URL via fetcher.get
    - parses with brand's parse_product_with_text(html, full_text, url, category)
    """
    url_list: Path = getattr(brand_module, "URL_LIST", None)
    if not url_list:
        print("[warn] manual runner missing URL_LIST in brand module")
        return []
    url_list = Path(url_list)
    if not url_list.exists():
        print(f"[warn] URL list not found: {url_list}")
        return []

    entries: List[tuple[str, str]] = []
    for line in url_list.read_text(encoding="utf-8-sig").splitlines():
        raw = line.strip().lstrip("\ufeff")
        if not raw:
            continue
        category = "manual"
        url = raw
        # Allow "category,url" or "category<TAB>url" format.
        for sep in (",", "\t"):
            if sep in raw:
                parts = raw.split(sep, 1)
                if len(parts) == 2:
                    category = parts[0].strip() or category
                    url = parts[1].strip()
                break
        if url:
            entries.append((category, url))

    products: List[Product] = []
    for category, url in entries:
        try:
            html = fetcher.get(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] fetch failed: {url} ({exc})")
            continue
        soup = BeautifulSoup(html, "html.parser")
        full_text = soup.get_text("\n", strip=True)
        product = brand_module.parse_product_with_text(
            html, full_text, url, category=category
        )
        if getattr(product, "image_url", None) is None:
            image_url = extract_image_url(soup=soup)
            if image_url:
                product.image_url = image_url
        if getattr(product, "name", None):
            products.append(product)
        else:
            print(f"[warn] skipped empty product: {url}")

    return products
