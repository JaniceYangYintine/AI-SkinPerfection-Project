# crawler/brands/sulwhasoo.py
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crawler.engine.models import Product

BRAND = "sulwhasoo"
DOMAIN = "https://tw.sulwhasoo.com"

# 🔑 人工維護的分類入口
CATEGORY_PAGES = {
    "清潔": "https://tw.sulwhasoo.com/skincare/category/cleansing.html",
    "養膚精華": "https://tw.sulwhasoo.com/skincare/category/first-care-serum.html",
    "化妝水": "https://tw.sulwhasoo.com/skincare/category/toner-mist.html",
    "乳液": "https://tw.sulwhasoo.com/skincare/category/lotion-emulsion.html",
    "精華液": "https://tw.sulwhasoo.com/skincare/category/serum-essence.html",
    "眼霜": "https://tw.sulwhasoo.com/skincare/category/eye-care.html",
    "乳霜": "https://tw.sulwhasoo.com/skincare/category/gel-cream.html",
    "面膜/特殊護理": "https://tw.sulwhasoo.com/skincare/category/mask-special-care.html",
    # "所有保養": "https://tw.sulwhasoo.com/skincare/category/all.html",
}


# ---------------------------
# utils
# ---------------------------
def _normalize_url(url: str) -> str:
    """移除 query 與 fragment，避免同頁不同參數重複"""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _is_product_path(href: str) -> bool:
    """
    雪花秀商品頁常見：/<slug>.html（一層路徑）
    排除：/skincare/category/*.html（分類頁）、以及非商品功能頁
    """
    if not href:
        return False

    href = href.strip()
    if href.startswith("javascript:") or href.startswith("#"):
        return False
    if href.startswith("mailto:") or href.startswith("tel:"):
        return False

    # 轉成 path 來判斷
    p = urlparse(href if href.startswith("http") else urljoin(DOMAIN, href))
    path = (p.path or "").strip()

    if not path.endswith(".html"):
        return False

    # 排除分類頁
    if "/category/" in path:
        return False

    # 排除常見非商品頁
    non_product_slugs = {
        "/sitemap.html",
        "/sitemap",
        "/customer-service.html",
        "/privacy-policy.html",
        "/terms-of-use.html",
        "/faq.html",
        "/contact.html",
        "/stores.html",
    }
    if path in non_product_slugs:
        return False

    # 商品頁多為只有一層：/something.html
    if path.count("/") != 1:
        return False

    return True


def _clean_price_to_digits(price: str | None) -> str | None:
    """把 'NT$2,880' / '2880' 變成 '2880'；抓不到回 None"""
    if not price:
        return None
    digits = re.sub(r"[^\d]", "", str(price))
    return digits or None


def _first_text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _find_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    """
    Magento 常見分頁：
      <a class="next" href="...p=2"> 或 rel=next
    找不到回 None
    """
    cand = soup.select_one(
        "link[rel='next'][href], a[rel='next'][href], a.next[href], li.pages-item-next a[href], a[title*='Next'][href]"
    )
    if not cand:
        return None
    href = (cand.get("href") or "").strip()
    if not href:
        return None
    return _normalize_url(urljoin(current_url, href))


# ---------------------------
# list pages → product urls
# ---------------------------
def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    """
    回傳：(category_key, product_url)
    - 嘗試翻頁（上限 30 頁避免卡）
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, entry_url in category_pages.items():
        page_url = entry_url
        page_count = 0

        while page_url and page_count < 30:
            page_count += 1
            html = fetcher.get(page_url)
            if not html:
                print(f"[SULWHASOO][warn] fetch category failed: {page_url}")
                break

            soup = BeautifulSoup(html, "html.parser")

            # Magento 類站型：商品卡常見 selector
            candidates = []
            candidates.extend(soup.select("a.product-item-link[href]"))
            candidates.extend(soup.select("a.product-item-photo[href]"))
            candidates.extend(soup.select("a.product.photo.product-item-photo[href]"))

            # fallback：全站 a[href]
            if not candidates:
                candidates = soup.select("a[href]")

            for a in candidates:
                href = (a.get("href") or "").strip()
                if not href:
                    continue
                if not _is_product_path(href):
                    continue

                full_url = href if href.startswith("http") else urljoin(page_url, href)
                full_url = _normalize_url(full_url)

                # 只收本站
                host = urlparse(full_url).netloc
                if host and host not in urlparse(DOMAIN).netloc:
                    continue

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


# ---------------------------
# product page parse
# ---------------------------
def _parse_jsonld_product(soup: BeautifulSoup) -> dict:
    """若站方有 Product JSON-LD 就用（更穩）；沒有就回 {}"""
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
            t = obj.get("@type")
            is_product = (t == "Product") or (isinstance(t, list) and "Product" in t)
            if is_product:
                return obj
    return {}


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    j = _parse_jsonld_product(soup)

    # 品名：JSON-LD → h1.page-title/span.base → 第一個 h1
    name = (j.get("name") or "").strip()
    if not name:
        h1 = soup.select_one("h1.page-title span.base") or soup.select_one("h1.page-title") or soup.select_one("h1")
        name = _first_text(h1)

    # 價格：JSON-LD offers → Magento price DOM → fallback regex
    price = None
    offers = j.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
    elif isinstance(offers, list) and offers and isinstance(offers[0], dict):
        price = offers[0].get("price") or offers[0].get("lowPrice")

    if price is None:
        price_el = (
            soup.select_one("div.product-info-price span.price")
            or soup.select_one("span.price-wrapper span.price")
            or soup.select_one("span.price")
        )
        price = _first_text(price_el)

    if price is None:
        txt = soup.get_text(" ", strip=True)
        m = re.search(r"NT\$\s?[\d,]+", txt)
        price = m.group(0) if m else None

    price = _clean_price_to_digits(price)

    # 描述：JSON-LD → meta → short description
    description = (j.get("description") or "").strip()
    if not description:
        meta = soup.select_one("meta[property='og:description'], meta[name='description']")
        description = (meta.get("content", "").strip() if meta else "")

    if not description:
        desc_el = soup.select_one(
            ".product.attribute.overview, .product.attribute.description, .product-info-main .value"
        )
        description = _first_text(desc_el)

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,
        description=description,
        url=_normalize_url(url),
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# =========================
# ✅ CLI Runner entrypoint（照 Clinique 模板加進度）
# =========================
def run(fetcher, stage: str = "stage1"):
    print("[SULWHASOO] run() start")

    category_pages = globals().get("CATEGORY_PAGES", None)
    if not category_pages:
        raise RuntimeError("[SULWHASOO] CATEGORY_PAGES not found")

    print(f"[SULWHASOO] categories: {len(category_pages)}")

    # 1️⃣ 抓商品 URL（這一步最常卡）
    print("[SULWHASOO] fetching product urls by category...")
    pairs = get_product_urls_by_category(fetcher, category_pages)
    print("[SULWHASOO] product urls fetched")

    product_pairs = list(pairs)
    print(f"[SULWHASOO] total products: {len(product_pairs)}")

    products: list[Product] = []

    # 2️⃣ 逐一抓商品頁（加 index log）
    for idx, (category, url) in enumerate(product_pairs, start=1):
        print(f"[SULWHASOO] ({idx}/{len(product_pairs)}) fetch product: {url}")

        html = fetcher.get(url)
        if not html:
            print(f"[SULWHASOO][warn] fetch failed: {url}")
            continue

        try:
            p = parse_product(html, url, category)
            if p and p.name:
                products.append(p)
        except Exception as e:
            print(f"[SULWHASOO][warn] parse failed: {url} ({type(e).__name__}: {e})")
            continue

    print(f"[SULWHASOO] run() finished, products={len(products)}")
    return products


# ✅ 單檔快速測試
if __name__ == "__main__":
    from crawler.engine.fetch import Fetcher

    f = Fetcher()
    pairs = get_product_urls_by_category(f, {"清潔": CATEGORY_PAGES["清潔"]})
    print("count:", len(pairs))
    print("sample:", pairs[:10])
