# crawler/brands/shiseido.py
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crawler.engine.models import Product

BRAND = "shiseido"
DOMAIN = "https://www.global-shiseido.com.tw"

CATEGORY_PAGES = {
    "精華液": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_serums/",
    "化妝水": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_balancinglotions/",
    "乳霜/保濕乳霜/日霜/晚霜": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_moisturizerscreams/",
    "乳液": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_moisturizerslotions/",
    "防禦修護": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_powerinfusing/",
    "洗面乳": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_makeupremovers/",
    "眼霜": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_eyelipcare/",
    "防曬": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_sunprotection/",
    "面膜": "https://www.global-shiseido.com.tw/axe_skincare/s1_category/s2_category_masks/",
}

PRODUCT_PATH_RE = re.compile(r"-\d{6,}\.html$", re.IGNORECASE)


def _normalize_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _is_product_url(href: str) -> bool:
    if not href:
        return False
    low = href.strip().lower()
    if low.startswith("#") or low.startswith("javascript:"):
        return False
    if low.startswith("mailto:") or low.startswith("tel:"):
        return False

    full = href if low.startswith("http") else urljoin(DOMAIN + "/", href)
    p = urlparse(full)

    if not p.netloc.endswith("global-shiseido.com.tw"):
        return False

    path = (p.path or "").rstrip("/")
    if not path.lower().endswith(".html"):
        return False

    if "/axe_skincare/" in path.lower():
        return False

    return PRODUCT_PATH_RE.search(path) is not None


def _find_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    cand = soup.select_one(
        "link[rel='next'][href], a[rel='next'][href], a.next[href], li.next a[href], a[aria-label*='Next'][href]"
    )
    if not cand:
        return None
    href = (cand.get("href") or "").strip()
    if not href:
        return None
    return _normalize_url(urljoin(current_url, href))


def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, entry_url in category_pages.items():
        page_url = entry_url
        page_count = 0

        while page_url and page_count < 20:
            page_count += 1
            html = fetcher.get(page_url)
            if not html:
                print(f"[SHISEIDO][warn] fetch failed: {page_url}")
                break

            soup = BeautifulSoup(html, "lxml")

            for a in soup.select("a[href]"):
                href = (a.get("href") or "").strip()
                if not href:
                    continue
                if not _is_product_url(href):
                    continue

                full_url = href if href.lower().startswith("http") else urljoin(page_url, href)
                full_url = _normalize_url(full_url)

                key = (category, full_url)
                if key in seen:
                    continue
                seen.add(key)
                results.append((category, full_url))

            next_url = _find_next_page_url(soup, page_url)
            if not next_url or next_url == page_url:
                break
            page_url = next_url

    return results


def _parse_jsonld_product(soup: BeautifulSoup) -> dict:
    for tag in soup.select('script[type="application/ld+json"]'):
        raw = tag.get_text(strip=True)
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        candidates: list[dict] = []
        if isinstance(data, list):
            candidates.extend([x for x in data if isinstance(x, dict)])
        elif isinstance(data, dict):
            candidates.append(data)
            g = data.get("@graph")
            if isinstance(g, list):
                candidates.extend([x for x in g if isinstance(x, dict)])

        for obj in candidates:
            t = obj.get("@type")
            is_product = (t == "Product") or (isinstance(t, list) and "Product" in t)
            if is_product:
                return obj

    return {}


def _clean_price_to_digits(price: str | None) -> str | None:
    if not price:
        return None
    digits = re.sub(r"[^\d]", "", str(price))
    return digits or None


def _extract_price_fallback(soup: BeautifulSoup) -> str | None:
    """
    補強：抓不到 JSON-LD/meta/DOM 時，再從 script / 全文抓數字
    """
    # 1) 一些站會把價格放在 data- attributes
    for sel in [
        "[data-price]",
        "[data-product-price]",
        "[data-sales-price]",
        "[data-base-price]",
    ]:
        el = soup.select_one(sel)
        if el:
            for key in ["data-price", "data-product-price", "data-sales-price", "data-base-price"]:
                v = el.get(key)
                if v and _clean_price_to_digits(v):
                    return v

    # 2) script 裡找 "price": 4300 或 "salesPrice": "4300"
    scripts = soup.find_all("script")
    for sc in scripts[:60]:  # 保守上限，避免太慢
        txt = (sc.string or sc.get_text() or "").strip()
        if not txt:
            continue
        m = re.search(r'"(?:salesPrice|price)"\s*:\s*"?(?P<p>\d{3,6})"?', txt)
        if m:
            return m.group("p")

    # 3) 全文找 NT$ 4,300
    text = soup.get_text(" ", strip=True)
    m = re.search(r"NT\$\s*[\d,]+", text)
    return m.group(0) if m else None


def _extract_description_fallback(soup: BeautifulSoup) -> str:
    """
    補強：meta 沒有時，抓常見 PDP 區塊
    """
    for sel in [
        ".product-short-description",
        ".short-description",
        ".product-description",
        ".description",
        "#description",
        "[data-qa='product-description']",
        ".pdp-description",
        ".product-detail",
        ".product-info",
        ".tabs-content .tab-content",
    ]:
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(" ", strip=True)
            if txt and len(txt) >= 10:
                return txt[:2000]
    return ""


def _extract_ingredients(soup: BeautifulSoup) -> str | None:
    """
    嘗試抓「成分/全成分/INCI」段落。抓不到就回 None（正常）
    """
    text = soup.get_text("\n", strip=True)
    for key in ["全成分", "成分", "INGREDIENTS", "INCI"]:
        if key in text:
            after = text.split(key, 1)[1].strip()
            # 常見切斷點（依你後續觀察可再加）
            for cut in ["使用方法", "HOW TO USE", "注意事項", "FAQ", "評論", "REVIEWS"]:
                if cut in after:
                    after = after.split(cut, 1)[0].strip()
            after = after.replace("\u3000", " ").strip()
            if after and len(after) >= 10:
                return after[:3000]
    return None


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "lxml")
    j = _parse_jsonld_product(soup)

    # name
    name = (j.get("name") or "").strip()
    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""
    if not name:
        ogt = soup.select_one("meta[property='og:title']")
        name = (ogt.get("content") or "").strip() if ogt else ""

    # price
    price = None
    offers = j.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
    elif isinstance(offers, list) and offers:
        first = offers[0]
        if isinstance(first, dict):
            price = first.get("price") or first.get("lowPrice")

    if price is None:
        meta_price = soup.select_one("meta[property='product:price:amount'], meta[itemprop='price']")
        if meta_price and meta_price.get("content"):
            price = meta_price["content"].strip()

    if price is None:
        price_el = soup.select_one(
            ".price, .product-price, .price__value, .value, [data-price], [data-product-price]"
        )
        if price_el:
            price = price_el.get_text(strip=True)

    if price is None:
        price = _extract_price_fallback(soup)

    price = _clean_price_to_digits(price)

    # description
    description = (j.get("description") or "").strip()
    if not description:
        meta = soup.select_one("meta[property='og:description'], meta[name='description']")
        description = (meta.get("content") or "").strip() if meta else ""
    if not description:
        description = _extract_description_fallback(soup)

    # ingredients（新增）
    ingredients = _extract_ingredients(soup)

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,
        description=description,
        url=_normalize_url(url),
        ingredients=ingredients,  # ✅ 你的 Product model / CSV 既然有這欄，就填它
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def run(fetcher, stage: str = "stage1"):
    print("[SHISEIDO] run() start")

    category_pages = globals().get("CATEGORY_PAGES", None)
    if not category_pages:
        raise RuntimeError("[SHISEIDO] CATEGORY_PAGES not found")

    print(f"[SHISEIDO] categories: {len(category_pages)}")

    print("[SHISEIDO] fetching product urls by category...")
    pairs = get_product_urls_by_category(fetcher, category_pages)
    print("[SHISEIDO] product urls fetched")

    product_pairs = list(pairs)
    print(f"[SHISEIDO] total products: {len(product_pairs)}")

    products: list[Product] = []

    for idx, (category, url) in enumerate(product_pairs, start=1):
        print(f"[SHISEIDO] ({idx}/{len(product_pairs)}) fetch product: {url}")

        html = fetcher.get(url)
        if not html:
            print(f"[SHISEIDO][warn] fetch failed: {url}")
            continue

        try:
            p = parse_product(html, url, category)
            if p:
                products.append(p)
        except Exception as e:
            print(f"[SHISEIDO][warn] parse failed: {url} ({type(e).__name__}: {e})")
            continue

    print(f"[SHISEIDO] run() finished, products={len(products)}")
    return products
