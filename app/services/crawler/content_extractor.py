from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup


def extract_text_content(
    html: str,
    content_selector: Optional[str] = None,
    remove_selectors: Optional[str] = None,
) -> str:
    soup = BeautifulSoup(html, "html.parser")

    if remove_selectors:
        for selector in [item.strip() for item in remove_selectors.split(",") if item.strip()]:
            for node in soup.select(selector):
                node.decompose()

    root = None
    if content_selector:
        root = soup.select_one(content_selector)
    if root is None:
        root = soup.find("article") or soup.find("main") or soup.body or soup

    paragraphs = [node.get_text(" ", strip=True) for node in root.find_all(["p", "li"])]
    if not paragraphs:
        text = root.get_text(" ", strip=True)
        return _normalize_whitespace(text)

    return _normalize_whitespace("\n".join(line for line in paragraphs if line))


def _normalize_whitespace(value: str) -> str:
    return "\n".join(part.strip() for part in value.splitlines() if part.strip())

