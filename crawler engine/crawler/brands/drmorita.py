# crawler/brands/drmorita.py
from __future__ import annotations

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime
import json
import re

from crawler.engine.models import Product

BRAND = "drmorita"
DOMAIN = "https://www.drmorita.com"
SHOP_ID = 41080

# 如果 sitemap 沒擋，根本不需要分類頁
SITEMAP_CANDIDATES = [
    f"{DOMAIN}/sitemap.xml",
    f"{DOMAIN}/sitemap_index.xml",
    f"{DOMAIN}/sitemap-index.xml",
]

# 仍保留分類頁（sitemap 失敗才用）
CATEGORY_PAGES = {
    "面膜": "https://www.drmorita.com/v2/official/SalePageCategory/391244?sortMode=Curator&lang=zh-TW",
    "化妝水/凝露": "https://www.drmorita.com/v2/official/SalePageCategory/394176?sortMode=Curator&lang=zh-TW",
    "精華液": "https://www.drmorita.com/v2/official/SalePageCategory/394177?sortMode=Curator&lang=zh-TW",
    "乳/霜": "https://www.drmorita.com/v2/official/SalePageCategory/394178?sortMode=Curator&lang=zh-TW",
    "洗面乳": "https://www.drmorita.com/v2/official/SalePageCategory/466867?sortMode=Curator",
}

SALEPAGE_RE = re.compile(r"/SalePage/(?:Index|index)/(\d+)", re.I)


def _normalize_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _canonical_product_url(pid: str) -> str:
    return f"{DOMAIN}/SalePage/Index/{pid}?lang=zh-TW"


def _clean_price(price) -> str | None:
    if price is None:
        return None
    digits = re.sub(r"[^\d]", "", str(price))
    return digits or None


def _safe_json_loads(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _looks_blocked(html: str) -> bool:
    low = html.lower()
    return any(k in low for k in [
        "cloudflare", "cf-challenge", "captcha",
        "access denied", "robot check"
    ])


def _polite_get(fetcher, url: str, referer: str | None = None) -> str:
    """
    盡量用你 fetcher 支援的參數（你前面已經在用 referer/min_delay/...）
    若你的 Fetcher 沒支援這些參數，請把這段改成 fetcher.get(url) 即可。
    """
    return fetcher.get(
        url,
        referer=referer or f"{DOMAIN}/?lang=zh-TW",
        min_delay=2.0,
        max_delay=4.0,
        retries=2,
    )


# -------------------------
# ✅ Sitemap pipeline
# -------------------------
def _extract_sitemap_urls_from_xml(xml_text: str) -> list[str]:
    """
    sitemap 或 sitemapindex 通常是 XML：
    - <urlset><url><loc>...</loc></url></urlset>
    - <sitemapindex><sitemap><loc>...</loc></sitemap></sitemapindex>
    """
    soup = BeautifulSoup(xml_text, "xml")
    locs = [loc.get_text(strip=True) for loc in soup.select("loc")]
    # 避免空字串
    return [u for u in locs if u and u.startswith("http")]


def _discover_sitemaps(fetcher) -> list[str]:
    """
    先抓 robots.txt 看有沒有 sitemap，再 fallback 到常見 sitemap 路徑
    """
    sitemaps: list[str] = []

    # 1) robots.txt
    try:
        robots = _polite_get(fetcher, f"{DOMAIN}/robots.txt", referer=f"{DOMAIN}/")
        for line in robots.splitlines():
            if line.lower().startswith("sitemap:"):
                sm = line.split(":", 1)[1].strip()
                if sm.startswith("http"):
                    sitemaps.append(sm)
    except Exception:
        pass

    # 2) 常見 sitemap 路徑
    for sm in SITEMAP_CANDIDATES:
        if sm not in sitemaps:
            sitemaps.append(sm)

    # 去重
    dedup = []
    seen = set()
    for u in sitemaps:
        if u in seen:
            continue
        seen.add(u)
        dedup.append(u)
    return dedup


def get_product_urls_from_sitemaps(fetcher) -> list[str]:
    """
    走 sitemap -> 找出所有 SalePage/Index/<id> 的 URL
    """
    sitemap_seeds = _discover_sitemaps(fetcher)
    print(f"[info] sitemap seeds: {sitemap_seeds}")

    product_urls: set[str] = set()
    visited_sitemaps: set[str] = set()

    # BFS：sitemapindex 會指向多個子 sitemap
    queue = list(sitemap_seeds)

    while queue:
        sm_url = queue.pop(0)
        if sm_url in visited_sitemaps:
            continue
        visited_sitemaps.add(sm_url)

        try:
            xml_text = _polite_get(fetcher, sm_url, referer=f"{DOMAIN}/")
        except Exception as e:
            print(f"[warn] sitemap fetch failed: {sm_url} ({e})")
            continue

        if _looks_blocked(xml_text):
            print(f"[warn] sitemap looks blocked: {sm_url}")
            continue

        locs = _extract_sitemap_urls_from_xml(xml_text)
        if not locs:
            continue

        # 如果 locs 裡面很多是 .xml，代表這個是 sitemap index
        xml_locs = [u for u in locs if u.lower().endswith(".xml")]
        if xml_locs:
            for u in xml_locs:
                if u not in visited_sitemaps:
                    queue.append(u)

        # 同時也可能直接包含網頁 URL
        for u in locs:
            m = SALEPAGE_RE.search(u)
            if not m:
                continue
            pid = m.group(1)
            product_urls.add(_canonical_product_url(pid))

    return sorted(product_urls)


# -------------------------
# Category fallback (你之前那套)
# -------------------------
def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for category, page_url in category_pages.items():
        print(f"[info] fetching category: {category}")
        html = _polite_get(fetcher, page_url, referer=f"{DOMAIN}/?lang=zh-TW")

        if _looks_blocked(html):
            print(f"[warn] category looks blocked: {page_url}")
            continue

        ids = set(SALEPAGE_RE.findall(html))
        print(f"[info] {category} found ids: {len(ids)}")

        for pid in sorted(ids):
            url = _canonical_product_url(pid)
            if url in seen:
                continue
            seen.add(url)
            results.append((category, url))

    return results


# -------------------------
# Product parse (HTML + API fallback)
# -------------------------
def _extract_jsonld_product(soup: BeautifulSoup) -> dict:
    for tag in soup.select('script[type="application/ld+json"]'):
        data = _safe_json_loads(tag.get_text(strip=True))
        if not data:
            continue
        items = data if isinstance(data, list) else [data]
        for obj in items:
            if isinstance(obj, dict) and obj.get("@type") == "Product":
                return obj
    return {}


def _try_fetch_product_api(fetcher, pid: str) -> dict:
    apis = [
        f"{DOMAIN}/api/SalePage/GetSalePage?salePageId={pid}",
        f"{DOMAIN}/api/SalePage/GetSalePage?shopId={SHOP_ID}&salePageId={pid}",
        f"{DOMAIN}/v2/api/SalePage/GetSalePage?salePageId={pid}",
    ]
    for api in apis:
        try:
            txt = _polite_get(fetcher, api, referer=_canonical_product_url(pid))
            data = _safe_json_loads(txt)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def parse_product(fetcher, url: str, category: str) -> Product:
    html = _polite_get(fetcher, url, referer=f"{DOMAIN}/?lang=zh-TW")
    if _looks_blocked(html):
        raise RuntimeError("blocked product page")

    soup = BeautifulSoup(html, "html.parser")
    jld = _extract_jsonld_product(soup)

    name = (jld.get("name") or "").strip()
    description = (jld.get("description") or "").strip()
    price = None

    offers = jld.get("offers") if isinstance(jld, dict) else None
    if isinstance(offers, dict):
        price = offers.get("price")

    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""

    # API fallback
    if (not name or price is None) and (m := SALEPAGE_RE.search(url)):
        pid = m.group(1)
        api = _try_fetch_product_api(fetcher, pid)
        name = name or api.get("SalePageTitle") or api.get("Title") or api.get("Name") or ""
        description = description or api.get("Description") or api.get("ShortDescription") or ""
        price = price or api.get("SellingPrice") or api.get("Price") or api.get("SalePrice")

    return Product(
        brand=BRAND,
        category=category,
        name=name.strip(),
        price=_clean_price(price),
        description=description.strip(),
        url=url,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# -------------------------
# Runner
# -------------------------
def run(fetcher) -> list[Product]:
    # ✅ 1) sitemap 優先（最有機會避開分類頁防護）
    product_urls = get_product_urls_from_sitemaps(fetcher)
    print(f"[info] sitemap product urls: {len(product_urls)}")

    pairs: list[tuple[str, str]] = []

    if product_urls:
        # sitemap 沒有分類資訊，就先用 "未分類"
        pairs = [("未分類", u) for u in product_urls]
    else:
        # ✅ 2) sitemap 不行才用分類頁（你現在這步會被擋）
        pairs = get_product_urls_by_category(fetcher, CATEGORY_PAGES)

    print(f"[info] total urls to parse: {len(pairs)}")

    products: list[Product] = []
    seen = set()

    for category, url in pairs:
        if url in seen:
            continue
        seen.add(url)

        try:
            p = parse_product(fetcher, url, category)
            products.append(p)
        except Exception as e:
            print(f"[warn] parse failed: {url} ({e})")

    return products


if __name__ == "__main__":
    from crawler.engine.fetch import Fetcher

    f = Fetcher()

    urls = get_product_urls_from_sitemaps(f)
    print("sitemap urls:", len(urls), "sample:", urls[:10])

    if urls:
        p = parse_product(f, urls[0], "未分類")
        print(p)
