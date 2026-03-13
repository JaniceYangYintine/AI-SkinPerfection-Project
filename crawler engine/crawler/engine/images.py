"""Shared utilities for extracting image URLs from HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup


def extract_image_url(html: str | None = None, soup: BeautifulSoup | None = None) -> str | None:
    """
    Return a best-effort image URL using common meta tags or the first <img>.

    - Prefer og:image / twitter:image / image_src.
    - Fallback to itemprop="image" or the first <img src>.
    - Does not perform network requests; only inspects provided HTML.
    """
    if soup is None:
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")

    def _get_attr(node, key: str) -> str:
        val = node.get(key) if node else None
        return val.strip() if isinstance(val, str) else ""

    # Common meta tags
    meta = soup.select_one(
        "meta[property='og:image'], meta[name='og:image'], "
        "meta[name='twitter:image'], meta[property='twitter:image']"
    )
    url = _get_attr(meta, "content")
    if url:
        return url

    # <link rel="image_src" href="...">
    link = soup.select_one("link[rel='image_src']")
    url = _get_attr(link, "href")
    if url:
        return url

    # itemprop image
    item = soup.select_one("[itemprop='image']")
    url = _get_attr(item, "content") or _get_attr(item, "src")
    if url:
        return url

    # Fallback: first <img src>
    img = soup.select_one("img[src]")
    url = _get_attr(img, "src")
    return url or None
