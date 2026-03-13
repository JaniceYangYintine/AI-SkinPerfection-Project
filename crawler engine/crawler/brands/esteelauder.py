# crawler/brands/esteelauder.py
from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from crawler.engine.models import Product

BRAND = "esteelauder"

# ✅ 用「不含 www」當作主網域（避免 DNS 解析不到 www）
DOMAIN = "https://esteelauder.com.tw"

# ✅ 萬一你這台電腦/網路對主站解析也怪，會自動 fallback 到 m 站
FALLBACK_DOMAINS = [
    "https://esteelauder.com.tw",
    "https://m.esteelauder.com.tw",
]

# 🔑 人工維護的分類入口（挑「會真的列出商品」的 catalog 頁）
CATEGORY_PAGES = {
    "卸妝/潔顏": f"{DOMAIN}/products/684/product-catalog/skin-care/cleanser-makeup-remover",
    "化妝水": f"{DOMAIN}/products/26389/product-catalog/skin-care/toner-treatment-lotion",
    "精華液/安瓶": f"{DOMAIN}/products/689/product-catalog/skin-care/repair-serum",
    "乳液/乳霜": f"{DOMAIN}/products/688/product-catalog/skin-care/moisturizer",
    "眼周保養/眼霜": f"{DOMAIN}/products/685/product-catalog/skin-care/eyecare",
    "特效護理": f"{DOMAIN}/products/693/product-catalog/skin-care/targeted-treatment",
}


# ---------------------------
# utils
# ---------------------------
def _strip_www(netloc: str) -> str:
    return netloc[4:] if netloc.startswith("www.") else netloc


def _force_domain(url: str, base_domain: str) -> str:
    """把任何網址強制換到指定 domain（保留 path）"""
    p = urlparse(url)
    b = urlparse(base_domain)
    return urlunparse((b.scheme, b.netloc, p.path, "", "", ""))


def _normalize_url(url: str) -> str:
    """移除 query/fragment，並統一去掉 www，避免 DNS 解析失敗"""
    p = urlparse(url)
    netloc = _strip_www(p.netloc)
    return urlunparse((p.scheme, netloc, p.path, "", "", ""))


def _is_product_url(href: str) -> bool:
    """
    Estee Lauder TW 商品頁常見：
      /product/<group_id>/<product_id>/product-catalog/...
    排除：
      /products/<...>/product-catalog/...（列表/分類，不是商品）
    """
    if not href:
        return False
    low = href.lower().strip()

    if low.startswith(("javascript:", "mailto:", "tel:", "#")):
        return False

    if "/product/" not in low or "/product-catalog/" not in low:
        return False

    # 排除列表頁
    if re.search(r"/products/\d+/product-catalog/", low):
        return False

    # 確保形狀：/product/<num>/<num>/product-catalog/
    return re.search(r"/product/\d+/\d+/product-catalog/", low) is not None


def _safe_get(fetcher, url: str) -> str:
    """
    ✅ 任何 fetch 失敗（含 DNS 解析不到 www）：
    1) 先試移除 www
    2) 再試 m 站
    """
    try:
        return fetcher.get(url)
    except Exception:
        # 先去 www 再試一次
        u1 = _normalize_url(url)
        if u1 != url:
            return fetcher.get(u1)

        # 再依序嘗試 fallback domains
        for d in FALLBACK_DOMAINS:
            alt = _force_domain(url, d)
            alt = _normalize_url(alt)
            if alt == url:
                continue
            try:
                return fetcher.get(alt)
            except Exception:
                continue

        raise


# ---------------------------
# list pages → product urls
# ---------------------------
def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    """
    回傳：(category_key, product_url)
    策略：分類頁抓所有 a[href]，用 _is_product_url 過濾。
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        html = ""
        try:
            html = _safe_get(fetcher, page_url)
        except Exception as e:
            print(f"[ESTEELAUDER][warn] fetch category failed: {page_url} ({type(e).__name__}: {e})")
            continue

        if not html:
            print(f"[ESTEELAUDER][warn] empty category html: {page_url}")
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href or not _is_product_url(href):
                continue

            full_url = href if href.startswith("http") else urljoin(page_url, href)

            # ✅ 一律 normalize + 統一到主站 domain（不含 www）
            full_url = _normalize_url(full_url)
            full_url = _force_domain(full_url, DOMAIN)

            key = (category, full_url)
            if key in seen:
                continue
            seen.add(key)
            results.append((category, full_url))

    return results


# ---------------------------
# product page parse
# ---------------------------
def _clean_price_to_digits(price: str | None) -> str | None:
    """把 'NT$2,200' / 'NT$2,200 - NT$8,550' 轉成 '2200'（取第一個數字）"""
    if not price:
        return None
    s = str(price)
    m = re.search(r"nt\$\s*([\d,]+)", s, flags=re.I)
    if m:
        return re.sub(r"[^\d]", "", m.group(1))
    digits = re.findall(r"[\d,]+", s)
    return re.sub(r"[^\d]", "", digits[0]) if digits else None


def _extract_name(soup: BeautifulSoup) -> str:
    h1 = soup.select_one("h1")
    if h1:
        name = h1.get_text(strip=True)
        if name:
            return name
    return soup.title.get_text(strip=True) if soup.title else ""


def _extract_price_text(soup: BeautifulSoup) -> str | None:
    text = soup.get_text("\n", strip=True)
    m = re.search(r"NT\$\s*[\d,]+(?:\s*-\s*NT\$\s*[\d,]+)?", text, flags=re.I)
    return m.group(0) if m else None


def _extract_description(soup: BeautifulSoup) -> str:
    meta = soup.select_one("meta[name='description'], meta[property='og:description']")
    if meta and meta.get("content"):
        d = meta["content"].strip()
        if d:
            return d

    text = soup.get_text("\n", strip=True)
    if "產品詳情" in text:
        after = text.split("產品詳情", 1)[1].strip()
        for cut in ["評論", "官網獨家優惠", "註冊", "已有帳戶"]:
            if cut in after:
                after = after.split(cut, 1)[0].strip()
        return after[:1200]

    return text[:600]


def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")

    name = _extract_name(soup)
    raw_price = _extract_price_text(soup)
    price = _clean_price_to_digits(raw_price)
    description = _extract_description(soup)

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,
        description=description,
        url=_force_domain(_normalize_url(url), DOMAIN),
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# =========================
# ✅ CLI Runner entrypoint（照 Clinique 模板加進度）
# =========================
def run(fetcher, stage: str = "stage1"):
    print("[ESTEELAUDER] run() start")

    category_pages = globals().get("CATEGORY_PAGES", None)
    if not category_pages:
        raise RuntimeError("[ESTEELAUDER] CATEGORY_PAGES not found")

    print(f"[ESTEELAUDER] categories: {len(category_pages)}")

    # 1️⃣ 抓商品 URL
    print("[ESTEELAUDER] fetching product urls by category...")
    pairs = get_product_urls_by_category(fetcher, category_pages)
    print("[ESTEELAUDER] product urls fetched")

    product_pairs = list(pairs)
    print(f"[ESTEELAUDER] total products: {len(product_pairs)}")

    products: list[Product] = []

    # 2️⃣ 逐一抓商品頁（加 index log）
    for idx, (category, url) in enumerate(product_pairs, start=1):
        print(f"[ESTEELAUDER] ({idx}/{len(product_pairs)}) fetch product: {url}")

        try:
            html = _safe_get(fetcher, url)
        except Exception as e:
            print(f"[ESTEELAUDER][warn] fetch failed: {url} ({type(e).__name__}: {e})")
            continue

        if not html:
            print(f"[ESTEELAUDER][warn] empty html: {url}")
            continue

        try:
            p = parse_product(html, url, category)
            if p and p.name:
                products.append(p)
        except Exception as e:
            print(f"[ESTEELAUDER][warn] parse failed: {url} ({type(e).__name__}: {e})")
            continue

    print(f"[ESTEELAUDER] run() finished, products={len(products)}")
    return products


# ✅ 快速單檔測試（可留可刪）
if __name__ == "__main__":
    from crawler.engine.fetch import Fetcher

    f = Fetcher()
    pairs = get_product_urls_by_category(f, {"乳液/乳霜": CATEGORY_PAGES["乳液/乳霜"]})
    print("count:", len(pairs))
    print("sample:", pairs[:10])
