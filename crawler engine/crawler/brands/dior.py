# brands/dior.py
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime
import json

from crawler.engine.models import Product


BRAND = "DIOR"

DOMAIN = "https://www.dior.com"

CATEGORY_PAGES = {
    "精華液": "https://www.dior.com/zh_tw/beauty/%E8%AD%B7%E8%86%9A%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81%E9%A1%9E%E5%88%A5/%E7%B2%BE%E8%8F%AF%E6%B6%B2",
    "乳霜": "https://www.dior.com/zh_tw/beauty/%E8%AD%B7%E8%86%9A%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81%E9%A1%9E%E5%88%A5/%E4%B9%B3%E9%9C%9C",
    "眼唇護理": "https://www.dior.com/zh_tw/beauty/%E8%AD%B7%E8%86%9A%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81%E9%A1%9E%E5%88%A5/%E7%9C%BC%E5%94%87%E8%AD%B7%E7%90%86-1",
    "卸妝與清潔": "https://www.dior.com/zh_tw/beauty/%E8%AD%B7%E8%86%9A%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81%E9%A1%9E%E5%88%A5/%E5%8D%B8%E5%A6%9D%E8%88%87%E6%B8%85%E6%BD%94",
    "化妝水": "https://www.dior.com/zh_tw/beauty/%E8%AD%B7%E8%86%9A%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81%E9%A1%9E%E5%88%A5/%E5%8C%96%E5%A6%9D%E6%B0%B4",
    "男性保養": "https://www.dior.com/zh_tw/beauty/%E8%AD%B7%E8%86%9A%E4%BF%9D%E9%A4%8A/%E4%BE%9D%E7%94%A2%E5%93%81%E9%A1%9E%E5%88%A5/%E7%94%B7%E6%80%A7%E4%BF%9D%E9%A4%8A",
    "嬰幼兒肌膚": "https://www.dior.com/zh_tw/beauty/%E8%AD%B7%E8%86%9A%E4%BF%9D%E9%A4%8A/%E4%BF%9D%E9%A4%8A%E5%85%A8%E7%B3%BB%E5%88%97%E6%8E%A8%E8%96%A6/baby-dior",
}

def _normalize_url(url: str) -> str:
    """移除 query 與 fragment，避免重複"""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))

def get_product_urls_by_category(fetcher, category_pages: dict) -> list[tuple[str, str]]:
    """
    回傳：(category_key, product_url)
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for category, page_url in category_pages.items():
        html = fetcher.get(page_url)
        soup = BeautifulSoup(html, "html.parser")

        # Dior 很可能是 /beauty/products/ 類型；用較寬鬆條件抓
        links = soup.select('a[href]')
        for a in links:
            href = a.get("href", "").strip()
            if not href:
                continue

            # 過濾：只保留看起來像商品頁的連結
            if "/products/" not in href and "/beauty/products/" not in href:
                continue

            full_url = href if href.startswith("http") else urljoin(DOMAIN, href)
            full_url = _normalize_url(full_url)

            key = (category, full_url)
            if key in seen:
                continue
            seen.add(key)
            results.append((category, full_url))

    return results

def _parse_jsonld_product(soup: BeautifulSoup) -> dict:
    """嘗試從 JSON-LD 抓商品資料（最穩）"""
    for tag in soup.select('script[type="application/ld+json"]'):
        raw = tag.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        # JSON-LD 可能是 list 或 dict
        candidates = data if isinstance(data, list) else [data]
        for obj in candidates:
            if not isinstance(obj, dict):
                continue
            if obj.get("@type") in ("Product",) or (isinstance(obj.get("@type"), list) and "Product" in obj.get("@type")):
                return obj
    return {}

def parse_product(html: str, url: str, category: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")

    # 先用 JSON-LD
    j = _parse_jsonld_product(soup)

    name = (j.get("name") or "").strip()
    if not name:
        h1 = soup.select_one("h1")
        name = h1.get_text(strip=True) if h1 else ""

    price = None
    offers = j.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
        if price is not None:
            price = str(price).strip()

    # description：JSON-LD 或 meta
    description = (j.get("description") or "").strip()
    if not description:
        meta = soup.select_one("meta[property='og:description'], meta[name='description']")
        description = meta.get("content", "").strip() if meta else ""

    # image: JSON-LD image -> og:image -> first img tag
    image = None
    img = j.get("image")
    if isinstance(img, str):
        image = img.strip()
    elif isinstance(img, list) and img and isinstance(img[0], str):
        image = img[0].strip()

    if not image:
        og = soup.select_one("meta[property='og:image']")
        if og and og.get("content"):
            image = og["content"].strip()

    if not image:
        img_tag = soup.select_one("img[src]")
        if img_tag:
            image = img_tag.get("src")

    return Product(
        brand=BRAND,
        category=category,
        name=name,
        price=price,
        description=description,
        url=url,
        image=image,
        crawled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

# # ✅ 快速單檔測試：測試抓不抓得到商品網址（測完可保留或刪）
if __name__ == "__main__":
    from crawler.engine.fetch import Fetcher

    f = Fetcher()
    pairs = get_product_urls_by_category(f, {"化妝水": CATEGORY_PAGES["化妝水"]})
    print("count:", len(pairs))
    print("sample:", pairs[:10])
