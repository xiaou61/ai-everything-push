from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


@dataclass
class WebEntry:
    title: str
    link: str
    published_at: Optional[object] = None
    author: Optional[str] = None


def fetch_url_text(url: str, timeout: float = 20.0, headers: Optional[dict] = None) -> str:
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def extract_article_links(
    list_url: str,
    html: str,
    list_item_selector: Optional[str] = None,
    link_selector: Optional[str] = None,
) -> list[WebEntry]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    if list_item_selector:
        for item in soup.select(list_item_selector):
            target = item.select_one(link_selector) if link_selector else item.select_one("a[href]")
            if target is not None:
                candidates.append(target)
    else:
        selector = link_selector or "article a[href], h2 a[href], h3 a[href], a[href]"
        candidates = list(soup.select(selector))

    results: list[WebEntry] = []
    seen_links: set[str] = set()
    for tag in candidates:
        href = tag.get("href")
        if not href:
            continue
        absolute = urljoin(list_url, href)
        if absolute in seen_links:
            continue
        title = tag.get_text(" ", strip=True)
        if not title:
            continue
        seen_links.add(absolute)
        results.append(WebEntry(title=title, link=absolute))
    return results


def parse_headers_json(raw_headers: Optional[str]) -> Optional[dict]:
    if not raw_headers:
        return None
    try:
        value = json.loads(raw_headers)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None
