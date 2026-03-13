# crawler/brands/bioessence.py
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse, urlencode, parse_qsl

from bs4 import BeautifulSoup
from tqdm import tqdm

from crawler.engine.models import Product

BRAND = "BIOESSENCE"
DOMAIN = "https://www.bioessence.com.tw"

CATEGORY_PAGES = {
    "卸妝｜潔顏": "https://www.bioessence.com.tw/collections/%E5%8D%B8%E5%A6%9D%EF%BD%9C%E6%BD%94%E9%A1%8F",
    "化妝水｜噴霧": "https://www.bioessence.com.tw/collections/%E5%8C%96%E5%A6%9D%E6%B0%B4%EF%BD%9C%E5%99%B4%E9%9C%A7",
    "精華液｜精華油｜安瓶": "https://www.bioessence.com.tw/collections/%E7%B2%BE%E8%8F%AF%E6%B6%B2%EF%BD%9C%E7%B2%BE%E8%8F%AF%E6%B2%B9",
    "乳液｜乳霜": "https://www.bioessence.com.tw/collections/%E4%B9%B3%E6%B6%B2%EF%BD%9C%E4%B9%B3%E9%9C%9C",
    "面膜｜凍膜": "https://www.bioessence.com.tw/collections/%E9%9D%A2%E8%86%9C%EF%BD%9C%E5%87%8D%E8%86%9C",
    "防曬": "https://www.bioessence.com.tw/collections/%E9%98%B2%E6%9B%AC",
}


def _normalize_url(u: str) -> str:
    p = urlparse(u)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _extract_product_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []

    # 常見：a[href*="/products/"]
    for a in soup.select('a[href*="/products/"]'):
        href = a.get("href")
        if not href:
            continue
        full = urljoin(base_url, href)
        full = _normalize_url(full)
        if "/products/" in full:
            urls.append(full)

    # 有些會把 URL 放在 data-* 或 script 內（保險）
    if not urls:
        m = re.findall(r'["\'](\/products\/[^"\']+)["\']', html)
        for path in m:
            full = _normalize_url(urljoin(base_url, path))
            urls.append(full)

    # 去重保序
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _build_url_with_params(url: str, params: dict[str, str]) -> str:
    p = urlparse(url)
    q = dict(parse_qsl(p.query))
    q.update(params)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), p.fragment))


def _fetch_collection_products_via_sections(
    fetcher,
    collection_url: str,
    max_pages: int = 60,
) -> list[str]:
    """
    用 Shopify 的 ?sections=xxx 取回商品網格 HTML，再抽 /products/ 連結。
    即使 /products.json 404，這條常常仍可用。
    """
    # 常見 collection grid section id（逐一嘗試）
    section_candidates = [
        "main-collection-product-grid",
        "collection-template",
        "main",
        "main-collection",
    ]

    # 先找到「能成功回資料」的 section id
    working_section: str | None = None
    for sec in section_candidates:
        test_url = _build_url_with_params(collection_url, {"sections": sec})
        txt = fetcher.get(test_url, headers={"Referer": collection_url})
        if not txt:
            continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        if isinstance(data, dict) and len(data) > 0:
            working_section = sec
            break

    if not working_section:
        return []

    all_urls: list[str] = []

    for page in range(1, max_pages + 1):
        page_url = _build_url_with_params(
            collection_url,
            {"sections": working_section, "page": str(page)},
        )
        txt = fetcher.get(page_url, headers={"Referer": collection_url})
        if not txt:
            break

        try:
            data = json.loads(txt)
        except Exception:
            break

        # Shopify sections 會回：{ "<section_id>": "<html...>" , ... }
        # 把所有 value html 串起來抽產品
        html_blob = ""
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, str):
                    html_blob += v + "\n"

        urls = _extract_product_links(html_blob, collection_url)
        if not urls:
            break

        before = len(all_urls)
        for u in urls:
            if u not in all_urls:
                all_urls.append(u)

        # 沒新增 → 到底了
        if len(all_urls) == before:
            break

    return all_urls


def run(fetcher, stage: str = "stage1"):
    print("[BIOESSENCE] run() start")
    print(f"[BIOESSENCE] categories: {len(CATEGORY_PAGES)}")

    products: list[Product] = []

    for category, collection_url in CATEGORY_PAGES.items():
        print(f"[BIOESSENCE] category={category}")

        urls = _fetch_collection_products_via_sections(fetcher, collection_url, max_pages=80)
        print(f"[BIOESSENCE] urls in category: {len(urls)}")

        for u in tqdm(urls, desc=f"🧴 {category}", unit="product"):
            handle = u.split("/products/")[-1]
            products.append(
                Product(
                    brand=BRAND,
                    category=category,
                    name=handle,  # 名稱先用 handle（你若要真名，我也能幫你改成抓商品頁 title）
                    url=u,
                )
            )

    print(f"[BIOESSENCE] run() finished, products={len(products)}")
    return products
