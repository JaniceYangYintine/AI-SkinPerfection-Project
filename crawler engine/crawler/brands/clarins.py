"""Crawler for Clarins (Taiwan site)."""

import json
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from engine.models import Product

BRAND = "Clarins"
BASE_URL = "https://www.clarins.com.tw"

# Category pages provided by the user (face care lineup).
CATEGORY_PAGES: dict[str, str] = {
    "cleanser": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E6%B8%85%E6%BD%94%E7%B3%BB%E5%88%97-211/",
    "toner": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E5%8C%96%E5%A6%9D%E6%B0%B4-212/",
    "serum": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E7%B2%BE%E8%8F%AF%E6%B6%B2-240/",
    "day-cream": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E6%97%A5%E9%96%93%E4%B9%B3%E6%B6%B2/%E4%B9%B3%E9%9C%9C-220/",
    "night-cream": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E5%A4%9C%E9%96%93%E4%B9%B3%E6%B6%B2/%E4%B9%B3%E9%9C%9C-230/",
    "eye-care": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E7%9C%BC%E9%83%A8%E4%BF%9D%E9%A4%8A-280/",
    "exfoliation": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/%E8%87%89%E9%83%A8%E4%BF%9D%E9%A4%8A/%E5%8E%BB%E8%A7%92%E8%B3%AA-261/",
    "uv": f"{BASE_URL}/%E8%87%89%E9%83%A8%E8%88%87%E8%BA%AB%E9%AB%94%E4%BF%9D%E9%A4%8A/uv%E9%98%B2%E6%9B%AC-uv_protectors/",
}


def _normalize_url(url: str) -> str:
    """Drop query/fragment for stable product URLs."""
    clean = url.split("?", 1)[0]
    return clean.split("#", 1)[0]


def _format_price(price: object, currency: str | None) -> str | None:
    if price is None:
        return None
    try:
        val = float(price)
        price_str = str(int(val)) if val.is_integer() else str(val)
    except Exception:
        price_str = str(price)
    prefix = "NT$" if currency in (None, "TWD", "NTD") else f"{currency} "
    return f"{prefix}{price_str}"


def _iter_ldjson_items(soup: BeautifulSoup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                yield item


def _extract_from_ldjson(soup: BeautifulSoup) -> tuple[str, str | None, str]:
    """Return (name, price, description) using ProductGroup/Variant LD+JSON."""
    group_desc = ""
    for item in _iter_ldjson_items(soup):
        if item.get("@type") == "ProductGroup":
            group_desc = item.get("description") or group_desc
            variants = item.get("hasVariant") or []
            if isinstance(variants, list) and variants:
                variant = variants[0]
                if isinstance(variant, dict):
                    name = variant.get("name") or item.get("name") or ""
                    offers = variant.get("offers")
                    if isinstance(offers, list):
                        offers = offers[0] if offers else None
                    price = (
                        _format_price(
                            offers.get("price"),
                            offers.get("priceCurrency") if isinstance(offers, dict) else None,
                        )
                        if isinstance(offers, dict)
                        else None
                    )
                    desc = group_desc or item.get("description") or ""
                    return name, price, desc
            # fallback to group name when variants missing
            return item.get("name") or "", None, group_desc or item.get("description") or ""
        if item.get("@type") == "Product":
            name = item.get("name") or ""
            offers = item.get("offers")
            if isinstance(offers, list):
                offers = offers[0] if offers else None
            price = (
                _format_price(
                    offers.get("price"),
                    offers.get("priceCurrency") if isinstance(offers, dict) else None,
                )
                if isinstance(offers, dict)
                else None
            )
            desc = item.get("description") or ""
            return name, price, desc
    return "", None, ""


def get_product_urls_by_category(
    fetcher, category_pages: dict[str, str]
) -> list[tuple[str, str]]:
    """Return list of (category, product_url) pairs discovered on category pages."""
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        try:
            html = fetcher.get(page_url)
        except Exception as exc:  # noqa: BLE001 - keep resilient for dead categories
            print(f"[warn] clarins fetch failed: {page_url} ({exc})")
            continue
        soup = BeautifulSoup(html, "html.parser")

        # Product tiles use anchors ending with #pidXXXX; drop the fragment.
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "#pid" not in href:
                continue

            url = href.split("#", 1)[0]
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = urljoin(BASE_URL, url)

            url = _normalize_url(url)
            key = (category, url)
            if key in seen:
                continue
            seen.add(key)
            results.append(key)

    return results


def _extract_description(soup: BeautifulSoup, fallback: str) -> str:
    # Prefer on-page「關於產品」區塊。
    about = soup.select_one(".product-info__description")
    if about:
        txt = about.get_text(" ", strip=True)
        if txt:
            # Strip common trailing prompt text.
            txt = txt.replace("了解更多", "").strip()
            if txt:
                return txt

    if fallback:
        return fallback
    meta = soup.select_one("meta[property='og:description'], meta[name='description']")
    if meta and meta.get("content"):
        return meta["content"].strip()
    body = soup.select_one(".pdp-main .description, .description")
    if body:
        txt = body.get_text(" ", strip=True)
        if txt:
            return txt
    return ""


def _extract_from_text_blob(text: str, name: str = "") -> str:
    """Extract a longer description from rendered page text (including shadow DOM)."""
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Prefer block starting at key labels.
    for i, ln in enumerate(lines):
        if any(kw in ln for kw in ("膚質", "質地", "使用說明", "產品特點")):
            chunk = "\n".join(lines[i : i + 60])
            return chunk.strip()
    if name:
        idx = text.find(name)
        if idx != -1:
            return text[idx : idx + 2000].strip()
    # Fallback: return a longer chunk of visible text.
    joined = "\n".join(lines)
    return joined[:2000].strip()


def _needs_playwright(description: str) -> bool:
    """Heuristic: description too short/empty -> use Playwright rendering."""
    if not description:
        return True
    if len(description) < 120:
        return True
    for kw in ("膚質", "質地", "使用說明", "產品特點"):
        if kw in description:
            return False
    return False


class _PlaywrightSession:
    """Lightweight reusable Playwright browser for Clarins pages."""

    def __init__(self):
        self._p = None
        self._browser = None
        self._page = None

    def __enter__(self):
        self._p = sync_playwright().start()
        self._browser = self._p.chromium.launch(headless=True)
        self._page = self._browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            ),
            locale="zh-TW",
        )
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._browser:
            self._browser.close()
        if self._p:
            self._p.stop()
        self._browser = None
        self._p = None
        self._page = None

    def get(self, url: str) -> tuple[str, str]:
        """Render a product page, expand details if possible, and return (html, full_text)."""
        self._page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # Give scripts a moment to populate DOM.
        self._page.wait_for_timeout(3000)
        # Try to open the full details accordion if present.
        for text in ("查看產品詳情", "產品詳情"):
            try:
                self._page.click(f"text={text}", timeout=2000)
                self._page.wait_for_timeout(2000)
                break
            except Exception:
                continue
        # Collect visible text (includes shadow DOM rendered text via inner_text).
        full_text = self._page.inner_text("body")
        return self._page.content(), full_text


def parse_product(html: str, url: str, category: str) -> Product:
    """Parse a Clarins product page into a Product model."""
    soup = BeautifulSoup(html, "html.parser")

    ld_name, ld_price, ld_desc = _extract_from_ldjson(soup)

    name_node = soup.select_one("h1, .pdp-main h1")
    name = ld_name or (name_node.get_text(strip=True) if name_node else "")
    price = ld_price
    if not price:
        price_node = soup.select_one("[itemprop='price'], .sales-price, .price")
        if price_node:
            txt = price_node.get_text(" ", strip=True)
            if txt:
                price = txt

    description = _extract_description(soup, ld_desc)
    image_url = None
    # LD+JSON image
    if ldjson := next(_iter_ldjson_items(soup), None):
        img = None
        if isinstance(ldjson, dict):
            img = ldjson.get("image")
            if isinstance(img, list) and img:
                img = img[0]
        if isinstance(img, str):
            image_url = img.strip()
    # Meta image fallback
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


def run(fetcher) -> list[Product]:
    """
    Clarins needs JS rendering to expose完整「關於產品」內容，因此這裡自行用
    Playwright 取得商品頁 HTML，再使用內建解析。
    """
    # 先用傳入的 fetcher (requests) 取得商品連結。
    pairs = get_product_urls_by_category(fetcher, CATEGORY_PAGES)
    deduped = list(dict.fromkeys((c, u) for c, u in pairs))

    products: list[Product] = []
    ps: _PlaywrightSession | None = None

    for category, url in deduped:
        # Step 1: 快速嘗試 requests 版
        product: Product | None = None
        try:
            html = fetcher.get(url)
            product = parse_product(html, url, category)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] clarins fetch failed: {url} ({exc})")
            product = None

        need_pw = _needs_playwright(getattr(product, "description", "") if product else "")

        # Step 2: 若描述不足，再用 Playwright 取完整「關於產品」
        if need_pw:
            if ps is None:
                ps = _PlaywrightSession().__enter__()
            try:
                html, full_text = ps.get(url)
                product = parse_product(html, url, category)
                # If description still weak, try shadow DOM text.
                if _needs_playwright(getattr(product, "description", "")):
                    enriched = _extract_from_text_blob(full_text, getattr(product, "name", ""))
                    if enriched:
                        product.description = enriched
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] clarins playwright failed: {url} ({exc})")
                continue

        if product and getattr(product, "name", None):
            products.append(product)
        else:
            print(f"[warn] clarins skipped empty product: {url}")

    if ps:
        ps.__exit__(None, None, None)

    return products
