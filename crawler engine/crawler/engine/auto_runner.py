"""Shared runner that executes a brand crawler module."""

from typing import Any

from engine.models import Product
from engine.images import extract_image_url


class Runner:
    def __init__(self, fetcher: Any):
        self.fetcher = fetcher

    def _fetch_html(self, url: str) -> str | None:
        try:
            return self.fetcher.get(url)
        except Exception as exc:  # noqa: BLE001 - keep simple for CLI logging
            print(f"[warn] fetch failed: {url} ({exc})")
            return None

    def _parse_product(self, brand_module, html: str, url: str, category: str) -> Product | None:
        try:
            return brand_module.parse_product(html, url, category)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] parse failed: {url} ({exc})")
            return None

    def run_brand(self, brand_module, *, limit: int | None = None) -> list[Product]:
        """
        Execute a brand module that exposes:
        - BRAND
        - CATEGORY_PAGES
        - get_product_urls_by_category(fetcher, CATEGORY_PAGES) -> [(category, url)]
        - parse_product(html, url, category) -> Product
        """
        pairs = brand_module.get_product_urls_by_category(
            self.fetcher, brand_module.CATEGORY_PAGES
        )

        deduped = list(dict.fromkeys((category, url) for category, url in pairs))

        if limit is not None:
            deduped = deduped[:limit]

        products: list[Product] = []
        for category, url in deduped:
            html = self._fetch_html(url)
            if not html:
                continue

            product = self._parse_product(brand_module, html, url, category)
            if not product:
                continue

            if not getattr(product, "image_url", None):
                image_url = extract_image_url(html)
                if image_url:
                    product.image_url = image_url

            if product and getattr(product, "name", None):
                products.append(product)
            else:
                print(f"[warn] skipped empty product: {url}")

        return products
