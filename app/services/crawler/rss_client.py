from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from xml.etree import ElementTree

import httpx


@dataclass
class FeedEntry:
    title: str
    link: str
    published_at: Optional[datetime] = None
    author: Optional[str] = None


def fetch_url_text(url: str, timeout: float = 20.0) -> str:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def fetch_feed_entries(url: str) -> list[FeedEntry]:
    return parse_feed_entries(fetch_url_text(url))


def parse_feed_entries(raw_xml: str) -> list[FeedEntry]:
    root = ElementTree.fromstring(raw_xml)
    items = root.findall(".//item")
    if items:
        return [_parse_rss_item(item) for item in items if _parse_rss_item(item).link]

    entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    if entries:
        result: list[FeedEntry] = []
        for entry in entries:
            parsed = _parse_atom_entry(entry)
            if parsed.link:
                result.append(parsed)
        return result

    return []


def _parse_rss_item(item: ElementTree.Element) -> FeedEntry:
    title = _text(item.find("title"))
    link = _text(item.find("link"))
    pub_date = _text(item.find("pubDate"))
    author = _text(item.find("author")) or _text(item.find("{http://purl.org/dc/elements/1.1/}creator"))
    return FeedEntry(
        title=title or "未命名文章",
        link=link or "",
        published_at=_parse_datetime(pub_date),
        author=author,
    )


def _parse_atom_entry(entry: ElementTree.Element) -> FeedEntry:
    title = _text(entry.find("{http://www.w3.org/2005/Atom}title"))
    link_element = entry.find("{http://www.w3.org/2005/Atom}link")
    link = link_element.attrib.get("href", "") if link_element is not None else ""
    published = _text(entry.find("{http://www.w3.org/2005/Atom}published")) or _text(
        entry.find("{http://www.w3.org/2005/Atom}updated")
    )
    author_name = entry.find(".//{http://www.w3.org/2005/Atom}name")
    return FeedEntry(
        title=title or "未命名文章",
        link=link,
        published_at=_parse_datetime(published),
        author=_text(author_name),
    )


def _text(node: Optional[ElementTree.Element]) -> Optional[str]:
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def _parse_datetime(raw_value: Optional[str]) -> Optional[datetime]:
    if not raw_value:
        return None
    try:
        return parsedate_to_datetime(raw_value)
    except (TypeError, ValueError, IndexError, OverflowError):
        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            return None

