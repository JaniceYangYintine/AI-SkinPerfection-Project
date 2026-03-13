# stageX_official_ingredients: fetch ingredients from official product pages
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from urllib.parse import urlparse

from crawler.engine.fetch import Fetcher


DEFAULT_STAGE2_GLOB = "stage2*.xlsx"

INGREDIENT_LABELS = [
    "成分",
    "全成分",
    "產品成分",
    "產品成份",
    "主要成分",
    "Ingredients",
    "INGREDIENTS",
    "INCI",
]
ALLOWED_DOMAINS = {
    "www.clarins.com.tw",
    # "www.lorealparis.com.tw",
    # "www.neutrogena.com.tw",
    # "www.paulaschoice.com.tw",
}


def _clean_text(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _score_candidate(text: str) -> int:
    if not text:
        return 0
    seps = sum(text.count(c) for c in [",", "、", ";", "；", "|", "•"])
    return seps * 5 + min(len(text), 200)


def _extract_paulas_choice(soup: BeautifulSoup) -> str | None:
    label = soup.find(string=lambda s: s and "\u7522\u54c1\u6210\u5206" in s)
    if label:
        nxt = label.find_parent().find_next(
            lambda tag: tag.name == "div"
            and tag.get("class")
            and any("sell_content_text" in c for c in tag.get("class", []))
        )
        if nxt:
            text = _clean_text(nxt.get_text(" ", strip=True))
            if len(text) >= 10:
                return text
    return None


def _extract_clarins(soup: BeautifulSoup) -> str | None:
    # Prefer the "產品成分" accordion section content.
    acc = soup.select_one(".accordion-section__content .composition-accordion p.text-uppercase")
    if acc:
        text = _clean_text(acc.get_text(" ", strip=True))
        if len(text) >= 50 and "," in text:
            return text
    for p in soup.find_all("p", class_="text-uppercase"):
        text = _clean_text(p.get_text(" ", strip=True))
        if len(text) >= 50 and "," in text:
            return text
    return None


def _extract_neutrogena(soup: BeautifulSoup) -> str | None:
    for p in soup.find_all("p"):
        text = _clean_text(p.get_text(" ", strip=True))
        if len(text) < 80 or text.count(",") < 8:
            continue
        # Heuristic: ingredients are typically mostly uppercase letters and commas.
        upper_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if upper_ratio >= 0.25:
            return text
    return None


def extract_ingredients_from_html(html: str, url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    url_lower = url.lower()
    if "clarins.com.tw" in url_lower:
        found = _extract_clarins(soup)
        if found:
            return found
    if "neutrogena.com.tw" in url_lower:
        found = _extract_neutrogena(soup)
        if found:
            return found
    if "paulaschoice.com.tw" in url_lower:
        found = _extract_paulas_choice(soup)
        if found:
            return found

    candidates: list[str] = []

    # 1) Look for labels and take text after the label or nearby sibling.
    label_pattern = re.compile("|".join(re.escape(k) for k in INGREDIENT_LABELS))
    for node in soup.find_all(string=label_pattern):
        parent = node.parent
        if not parent:
            continue
        text = _clean_text(parent.get_text(" ", strip=True))
        if text:
            for label in INGREDIENT_LABELS:
                if label in text:
                    after = text.split(label, 1)[-1].lstrip(":： ")
                    if len(after) >= 10:
                        candidates.append(after)
        # Try next element text
        nxt = parent.find_next()
        if nxt:
            nxt_text = _clean_text(nxt.get_text(" ", strip=True))
            if len(nxt_text) >= 10:
                candidates.append(nxt_text)

    # 2) Look for ingredient-like containers by id/class.
    for elem in soup.find_all(True, {"id": re.compile(r"ingredient|inci", re.I)}):
        candidates.append(_clean_text(elem.get_text(" ", strip=True)))
    for elem in soup.find_all(True, {"class": re.compile(r"ingredient|inci", re.I)}):
        candidates.append(_clean_text(elem.get_text(" ", strip=True)))

    # 3) Pick the best candidate.
    candidates = [c for c in candidates if 10 <= len(c) <= 2000]
    if not candidates:
        return None
    best = max(candidates, key=_score_candidate)
    return best or None


def _clarins_playwright_extract(url: str) -> str | None:
    # Deprecated: use _ClarinsPlaywrightSession for reuse.
    return None


class _ClarinsPlaywrightSession:
    """Reusable Playwright browser for Clarins composition extraction."""

    def __init__(self):
        self._p = None
        self._browser = None
        self._page = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright

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

    def get_ingredients(self, url: str) -> str | None:
        page = self._page
        if page is None:
            return None
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        # Try opening the composition accordion.
        try:
            if page.locator("[data-auto-id='composition-title']").count() > 0:
                page.click("[data-auto-id='composition-title']", timeout=3000)
            else:
                page.locator("text=產品成分").first.click(timeout=3000)
            page.wait_for_timeout(1500)
        except Exception:
            pass
        # Wait for ingredient block to appear.
        try:
            page.wait_for_selector(
                ".composition-accordion p.text-uppercase",
                timeout=8000,
            )
        except Exception:
            pass
        soup = BeautifulSoup(page.content(), "html.parser")
        return _extract_clarins(soup)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent / "output"
    if args.input:
        input_path = base_dir / args.input
    else:
        candidates = list(base_dir.glob(DEFAULT_STAGE2_GLOB))
        if not candidates:
            raise FileNotFoundError(f"No files match {DEFAULT_STAGE2_GLOB}")
        input_path = max(candidates, key=lambda p: p.stat().st_mtime)

    df = pd.read_excel(input_path, sheet_name=0)
    if "商品網址" not in df.columns:
        raise ValueError("Missing 商品網址 column")

    fetcher = Fetcher()
    results = []
    clarins_session = None
    try:
        clarins_session = _ClarinsPlaywrightSession().__enter__()
    except Exception:
        clarins_session = None
    for url in df["商品網址"].tolist():
        if pd.isna(url) or not str(url).strip():
            results.append("")
            continue
        try:
            url_str = str(url).strip()
            domain = urlparse(url_str).netloc.lower()
            if domain not in ALLOWED_DOMAINS:
                results.append("")
                continue
            if domain == "www.clarins.com.tw":
                # Clarins requires JS rendering for the composition accordion.
                ing = (
                    clarins_session.get_ingredients(url_str)
                    if clarins_session
                    else ""
                )
                if not ing:
                    html = fetcher.get(url_str)
                    ing = extract_ingredients_from_html(html, url_str)
            else:
                html = fetcher.get(url_str)
                ing = extract_ingredients_from_html(html, url_str)
            results.append(ing or "")
        except Exception:
            results.append("")
    if clarins_session:
        clarins_session.__exit__(None, None, None)

    df["ingredients_official"] = results

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = args.output or f"stageX_official_ingredients_{stamp}.xlsx"
    out_path = base_dir / out_name
    df.to_excel(out_path, index=False)
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# python crawler\stageX_official_ingredients.py
