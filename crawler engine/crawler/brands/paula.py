"""Crawler for Paula's Choice products - 修正產品 ID 提取問題"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from engine.models import Product

BRAND = "Paula's Choice"

BASE_URL = "https://www.paulaschoice.com.tw"
API_PRODUCTS = "https://api.paulaschoice.com.tw/front-stage/v1/get-open-products"
API_SELL_PAGE = (
    "https://api.paulaschoice.com.tw/front-stage/v1/get-sell-pages/{slug}"
)

# 對照站上分類 slug -> 中文分類名稱
CATEGORY_LABELS: Dict[str, str] = {
    "toner": "化妝水",
    "cleanser": "卸妝 洗臉",
    "exfoliant": "去角質",
    "serum": "精華液",
    "booster": "高濃度精粹",
    "eye-cream": "眼霜",
    "moisturizer": "乳液／乳霜",
    "sunscreen": "防曬",
}

# 供 main/runner 介面使用
CATEGORY_PAGES: dict[str, str] = {
    slug: f"{BASE_URL}/{slug}" for slug in CATEGORY_LABELS.keys()
}


def _parse_href(href: str) -> Tuple[str, str, str]:
    """
    由 API 回傳的 href 推出分類 slug、商品 slug 和產品 ID。
    
    修正重點: href 格式是 "category/product-slug/product_id"
    例如: "serum/skin-balancing-super-antioxidant-concentrate-serum/3350"
    
    Returns:
        (category, slug, product_id)
        例如: ("serum", "skin-balancing-super-antioxidant-concentrate-serum", "3350")
    """
    parts = [p for p in href.split("/") if p]
    category = parts[0] if len(parts) >= 1 else ""
    slug = parts[1] if len(parts) >= 2 else ""
    product_id = parts[2] if len(parts) >= 3 else ""  # ← 新增:第三部分是產品 ID
    return category, slug, product_id


def _normalize_image_url(url: str | None) -> str | None:
    """Ensure image URL is absolute and trimmed."""
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        url = f"https:{url}"
    elif url.startswith("/"):
        url = urljoin(BASE_URL, url)
    return url


def _is_product_image(url: str) -> bool:
    """判斷是否為商品圖片 URL"""
    if not url:
        return False
    
    url_lower = url.lower()
    
    # 排除廣告和其他非商品圖
    exclude_patterns = ['/lp/ads/', '/logo', '/icon', '/banner', '/promotion']
    if any(pattern in url_lower for pattern in exclude_patterns):
        return False
    
    # 商品圖特徵
    product_patterns = ['sku_', '/upload/pd', '/pd600_new/']
    return any(pattern in url_lower for pattern in product_patterns)


def _extract_image_url(soup: BeautifulSoup, pid: str = None) -> str | None:
    """優先抓取商品圖片,避免抓到廣告橫幅。"""
    
    # 策略 1: 如果有 pid,直接構建標準圖片 URL (最可靠)
    if pid:
        return f"https://fs.paulaschoice.com.tw/upload/pd600_new/SKU_{pid}.jpg"
    
    # 策略 2: 優先檢查 data-* 屬性 (lazy loading)
    data_attrs = [
        'data-zoom-src',
        'data-large', 
        'data-src',
        'data-original',
        'data-lazy',
    ]
    
    for img in soup.select('img'):
        for attr in data_attrs:
            val = img.get(attr, '').strip()
            if val and _is_product_image(val):
                return val
    
    # 策略 3: 檢查普通 src 屬性
    for img in soup.select('img'):
        val = img.get('src', '').strip()
        if val and _is_product_image(val):
            return val
    
    # 策略 4: 檢查 og:image
    meta_img = soup.select_one(
        "meta[property='og:image'], meta[name='og:image']"
    )
    if meta_img and meta_img.get("content"):
        val = meta_img.get("content", "").strip()
        if _is_product_image(val):
            return val
    
    # 策略 5: 檢查 srcset
    for img in soup.select("img"):
        srcset = img.get("srcset", "").strip()
        if srcset:
            for part in srcset.split(','):
                candidate = part.strip().split()[0] if part.strip() else ''
                if candidate and _is_product_image(candidate):
                    return candidate
    
    return None


def _fetch_sell_page(fetcher, slug: str) -> Tuple[str, str, str]:
    """從 sell-page API 取回描述/特色/功效;失敗則回傳空字串。"""
    if not slug:
        return "", "", ""

    url = API_SELL_PAGE.format(slug=slug)
    try:
        r = fetcher.session.get(url, timeout=fetcher.timeout)
        r.raise_for_status()
        payload = r.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] sell-page api failed: {url} ({exc})")
        return "", "", ""

    desc = ""
    feature = ""
    effect = ""

    def walk(obj: Any):
        nonlocal desc, feature, effect
        if desc and feature and effect:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                lk = k.lower()
                if lk == "sell_description" and not desc and isinstance(v, str):
                    desc = v
                elif lk == "sell_feature" and not feature and isinstance(v, str):
                    feature = v
                elif lk == "sell_effect" and not effect and isinstance(v, str):
                    effect = v
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(payload)
    return desc, feature, effect


def _extract_description(html: str) -> str:
    """Prefer p.text-grey4, fallback to og:description/meta description."""
    soup = BeautifulSoup(html, "html.parser")

    p = soup.select_one("p.text-grey4")
    if p:
        desc = p.get_text("\n", strip=True)
        if desc:
            return desc

    meta = soup.select_one('meta[property="og:description"], meta[name="description"]')
    if meta and meta.get("content"):
        return meta["content"].strip()

    return ""


def _extract_paula_fields(html: str) -> Tuple[str, str]:
    """Parse page to get sell_feature / sell_effect (DOM first, then JSON)."""
    soup = BeautifulSoup(html, "html.parser")

    feature = ""
    effect = ""

    dom_sections = soup.select("div.sell_content_text")
    if dom_sections:
        if len(dom_sections) >= 1:
            feature = dom_sections[0].get_text("\n", strip=True)
        if len(dom_sections) >= 2:
            effect = dom_sections[1].get_text("\n", strip=True)
        if feature and effect:
            return feature, effect

    data_node = soup.find("script", id="__NUXT_DATA__")
    if not data_node:
        return feature, effect

    raw_json = (data_node.string or data_node.get_text("", strip=False) or "").strip()
    if not raw_json:
        return feature, effect
    data: Any = None
    try:
        data = json.loads(raw_json)
    except Exception:
        data = None

    if data is None:
        m_feat = re.search(r'"sell_feature":\s*(?P<v>"(?:\\.|[^"])*"|\d+)', raw_json)
        m_eff = re.search(r'"sell_effect":\s*(?P<v>"(?:\\.|[^"])*"|\d+)', raw_json)
        if m_feat and not feature:
            v = m_feat.group("v")
            if v.startswith('"'):
                try:
                    feature = json.loads(v)
                except Exception:
                    feature = ""
        if m_eff and not effect:
            v = m_eff.group("v")
            if v.startswith('"'):
                try:
                    effect = json.loads(v)
                except Exception:
                    effect = ""
        return feature, effect

    def resolve(val: Any) -> Any:
        if isinstance(val, int) and isinstance(data, list) and 0 <= val < len(data):
            return data[val]
        return val

    def walk(obj: Any):
        nonlocal feature, effect
        if feature and effect:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "sell_feature" and not feature:
                    val = resolve(v)
                    if isinstance(val, str):
                        feature = val
                if k == "sell_effect" and not effect:
                    val = resolve(v)
                    if isinstance(val, str):
                        effect = val
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)

    if isinstance(data, list):
        if not feature and len(data) > 140 and isinstance(data[140], str):
            feature = data[140]
        if not effect and len(data) > 141 and isinstance(data[141], str):
            effect = data[141]

    return feature, effect


def run(fetcher) -> List[Product]:
    """
    主流程:用開放產品 API 取得列表,以 href 判斷分類與 slug,再進入產品頁/賣場頁抓取細節。
    """
    try:
        r = fetcher.session.get(
            API_PRODUCTS,
            headers={"Accept": "application/json"},
            timeout=fetcher.timeout,
        )
        r.raise_for_status()
        payload = r.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] products api failed: {API_PRODUCTS} ({exc})")
        return []

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    products: List[Product] = []

    for p in payload.get("products", []):
        href = p.get("href") or ""
        
        # ===== 修正重點 1: 從 href 提取正確的產品 ID =====
        category_slug, slug, product_id = _parse_href(href)  # ← 新增第三個返回值
        category = CATEGORY_LABELS.get(category_slug, category_slug)
        if category_slug not in CATEGORY_LABELS:
            continue

        # 備用: API 中的 p_id (但優先使用 href 中的 product_id)
        api_pid = p.get("p_id")
        pid = product_id or str(api_pid) if api_pid else None  # ← 優先使用 href 中的 ID
        
        url = href
        if url and not url.startswith("http"):
            url = f"{BASE_URL}/{url.lstrip('/')}"
        elif not url and pid:
            url = f"{BASE_URL}/product/{pid}"

        price = p.get("p_price")

        # ===== 修正重點 2: 使用正確的 pid 構建圖片 URL =====
        image_url = None
        if pid:
            image_url = f"https://fs.paulaschoice.com.tw/upload/pd600_new/SKU_{pid}.jpg"
            print(f"[info] 構建圖片 URL: {image_url} (pid={pid})")  # ← 調試用
        
        # 備用:從 API 取得
        if not image_url:
            p_photo = p.get("p_photo")
            if p_photo and _is_product_image(p_photo):
                image_url = _normalize_image_url(p_photo)

        api_desc, api_feature, api_effect = _fetch_sell_page(fetcher, slug)

        feature = api_feature
        effect = api_effect
        base_desc = api_desc or (p.get("p_note") or "").strip()

        if not feature or not effect or not base_desc:
            try:
                detail_html = fetcher.get(url)
                if not base_desc:
                    base_desc = _extract_description(detail_html)
                if not (feature and effect):
                    html_feature, html_effect = _extract_paula_fields(detail_html)
                    feature = feature or html_feature
                    effect = effect or html_effect
                
                # 最後手段:從網頁 HTML 提取圖片
                if not image_url:
                    soup = BeautifulSoup(detail_html, "html.parser")
                    img_url = _extract_image_url(soup, pid=pid)
                    if img_url:
                        image_url = _normalize_image_url(img_url)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] detail fetch failed: {url} ({exc})")

        # 將特色與功效合併到描述中
        full_desc_parts = []
        if base_desc:
            full_desc_parts.append(base_desc)
        if feature:
            full_desc_parts.append(f"產品特色: {feature}")
        if effect:
            full_desc_parts.append(f"產品功效: {effect}")

        product = Product(
            brand=BRAND,
            category=category,
            name=(p.get("p_name") or "").strip(),
            price=str(price) if price is not None else None,
            description="\n\n".join(full_desc_parts).strip(),
            url=url,
            image_url=image_url,
            crawled_at=now,
        )
        products.append(product)

    return products