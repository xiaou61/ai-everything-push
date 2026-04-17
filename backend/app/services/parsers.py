from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from app.core.config import Settings, get_settings
from app.models.entities import Source, SourceType


DEFAULT_DETAIL_CONTENT_SELECTORS = (
    "article",
    "main",
    ".article-content",
    ".post-content",
    ".entry-content",
    ".topic-body",
    ".markdown",
    ".content",
)
DEFAULT_DETAIL_AUTHOR_SELECTORS = (
    '[rel="author"]',
    ".author",
    ".byline",
    '[data-author]',
    'meta[name="author"]',
    'meta[property="article:author"]',
)


@dataclass(slots=True)
class ParsedEntry:
    external_id: str
    title: str
    url: str
    content: str
    author: str | None
    published_at: datetime | None
    raw_payload: dict[str, Any]


def html_to_text(value: str) -> str:
    soup = BeautifulSoup(value or "", "html.parser")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def extract_nested_value(payload: Any, path: str) -> Any:
    current: Any = payload
    for fragment in path.split("."):
        if isinstance(current, list):
            if not fragment.isdigit():
                return None
            index = int(fragment)
            if index >= len(current):
                return None
            current = current[index]
            continue

        if isinstance(current, dict):
            current = current.get(fragment)
            continue

        return None
    return current


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return date_parser.parse(str(value))
    except (ValueError, TypeError, OverflowError):
        return None


class SourceParserService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def fetch(self, source: Source) -> list[ParsedEntry]:
        if source.source_type == SourceType.RSS:
            return self._parse_rss(source)
        if source.source_type == SourceType.JSON:
            return self._parse_json(source)
        return self._parse_html(source)

    def _parse_rss(self, source: Source) -> list[ParsedEntry]:
        feed = feedparser.parse(source.url)
        items: list[ParsedEntry] = []
        for entry in feed.entries[: source.fetch_limit]:
            title = str(getattr(entry, "title", "")).strip()
            url = str(getattr(entry, "link", source.url)).strip()
            content = self._extract_rss_content(entry)

            parsed_entry = ParsedEntry(
                external_id=str(getattr(entry, "id", "")) or url or title,
                title=title or "未命名条目",
                url=url,
                content=content,
                author=str(getattr(entry, "author", "")).strip() or None,
                published_at=parse_datetime(getattr(entry, "published", None) or getattr(entry, "updated", None)),
                raw_payload=dict(entry),
            )
            items.append(self._enrich_entry_from_detail_page(source, parsed_entry))
        return items

    def _parse_json(self, source: Source) -> list[ParsedEntry]:
        response = httpx.get(source.url, timeout=self.settings.request_timeout_seconds)
        response.raise_for_status()
        payload = response.json()

        item_path = source.parser_config.get("items_path", "")
        items = extract_nested_value(payload, item_path) if item_path else payload
        if not isinstance(items, list):
            return []

        title_field = source.parser_config.get("title_field", "title")
        link_field = source.parser_config.get("link_field", "url")
        content_field = source.parser_config.get("content_field", "content")
        author_field = source.parser_config.get("author_field", "author")
        external_id_field = source.parser_config.get("external_id_field", "id")
        published_at_field = source.parser_config.get("published_at_field", "published_at")

        results: list[ParsedEntry] = []
        for item in items[: source.fetch_limit]:
            if not isinstance(item, dict):
                continue
            title = str(extract_nested_value(item, title_field) or "").strip()
            url = urljoin(source.url, str(extract_nested_value(item, link_field) or source.url))
            parsed_entry = ParsedEntry(
                external_id=str(extract_nested_value(item, external_id_field) or url or title),
                title=title or "未命名条目",
                url=url,
                content=html_to_text(str(extract_nested_value(item, content_field) or "").strip()),
                author=str(extract_nested_value(item, author_field) or "").strip() or None,
                published_at=parse_datetime(extract_nested_value(item, published_at_field)),
                raw_payload=item,
            )
            results.append(self._enrich_entry_from_detail_page(source, parsed_entry))
        return results

    def _parse_html(self, source: Source) -> list[ParsedEntry]:
        response = httpx.get(source.url, timeout=self.settings.request_timeout_seconds, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        item_selector = source.parser_config.get("item_selector")
        if not item_selector:
            return []

        title_selector = source.parser_config.get("title_selector", "a")
        link_selector = source.parser_config.get("link_selector", title_selector)
        content_selector = source.parser_config.get("content_selector")
        author_selector = source.parser_config.get("author_selector")
        published_at_selector = source.parser_config.get("published_at_selector")
        external_id_attr = source.parser_config.get("external_id_attr", "href")

        results: list[ParsedEntry] = []
        for item in soup.select(item_selector)[: source.fetch_limit]:
            title_node = item.select_one(title_selector)
            link_node = item.select_one(link_selector)
            content_node = item.select_one(content_selector) if content_selector else None
            author_node = item.select_one(author_selector) if author_selector else None
            published_at_node = item.select_one(published_at_selector) if published_at_selector else None

            if title_node is None or link_node is None:
                continue

            href = link_node.get("href") or title_node.get("href") or source.url
            title = title_node.get_text(" ", strip=True)
            external_id = link_node.get(external_id_attr) or href or title
            parsed_entry = ParsedEntry(
                external_id=str(external_id),
                title=title or "未命名条目",
                url=urljoin(source.url, href),
                content=html_to_text(str(content_node)) if content_node else "",
                author=author_node.get_text(" ", strip=True) if author_node else None,
                published_at=parse_datetime(published_at_node.get_text(" ", strip=True) if published_at_node else None),
                raw_payload={"html": str(item)},
            )
            results.append(self._enrich_entry_from_detail_page(source, parsed_entry))
        return results

    def _extract_rss_content(self, entry: Any) -> str:
        entry_content = getattr(entry, "content", None)
        if isinstance(entry_content, list) and entry_content:
            candidate = html_to_text(str(getattr(entry_content[0], "value", "")))
            if candidate:
                return candidate

        if getattr(entry, "summary", None):
            candidate = html_to_text(str(entry.summary))
            if candidate:
                return candidate

        if getattr(entry, "description", None):
            return html_to_text(str(entry.description))

        return ""

    def _enrich_entry_from_detail_page(self, source: Source, entry: ParsedEntry) -> ParsedEntry:
        detail_page_enabled = source.parser_config.get("detail_page_enabled", True)
        min_length = int(source.parser_config.get("detail_content_min_length", 140))
        needs_content = len(entry.content.strip()) < min_length
        needs_author = not entry.author
        if not detail_page_enabled or (not needs_content and not needs_author):
            return entry

        try:
            response = httpx.get(entry.url, timeout=self.settings.request_timeout_seconds, follow_redirects=True)
            response.raise_for_status()
        except Exception:
            return entry

        soup = BeautifulSoup(response.text, "html.parser")
        detail_content = self._extract_detail_content(soup, source) if needs_content else entry.content
        detail_author = self._extract_detail_author(soup, source) if needs_author else entry.author

        raw_payload = dict(entry.raw_payload)
        raw_payload["detail_page_enriched"] = bool(
            (detail_content and detail_content != entry.content) or (detail_author and detail_author != entry.author)
        )

        return ParsedEntry(
            external_id=entry.external_id,
            title=entry.title,
            url=entry.url,
            content=detail_content or entry.content,
            author=detail_author or entry.author,
            published_at=entry.published_at,
            raw_payload=raw_payload,
        )

    def _extract_detail_content(self, soup: BeautifulSoup, source: Source) -> str:
        selectors = self._get_selector_list(
            parser_config=source.parser_config,
            list_key="detail_page_content_selectors",
            single_key="detail_page_content_selector",
            default_value=DEFAULT_DETAIL_CONTENT_SELECTORS,
        )
        candidates: list[str] = []
        for selector in selectors:
            for node in soup.select(selector):
                text = html_to_text(str(node))
                if text:
                    candidates.append(text)

        if not candidates:
            body = soup.body or soup
            fallback_text = html_to_text(str(body))
            if fallback_text:
                candidates.append(fallback_text)

        return max(candidates, key=len) if candidates else ""

    def _extract_detail_author(self, soup: BeautifulSoup, source: Source) -> str | None:
        selectors = self._get_selector_list(
            parser_config=source.parser_config,
            list_key="detail_page_author_selectors",
            single_key="detail_page_author_selector",
            default_value=DEFAULT_DETAIL_AUTHOR_SELECTORS,
        )
        for selector in selectors:
            for node in soup.select(selector):
                if node.name == "meta":
                    content = (node.get("content") or "").strip()
                    if content:
                        return content
                text = (node.get_text(" ", strip=True) or node.get("data-author") or "").strip()
                if text:
                    return text
        return None

    def _get_selector_list(
        self,
        parser_config: dict[str, Any],
        list_key: str,
        single_key: str,
        default_value: tuple[str, ...],
    ) -> list[str]:
        list_value = parser_config.get(list_key)
        if isinstance(list_value, list):
            return [str(item).strip() for item in list_value if str(item).strip()]

        single_value = parser_config.get(single_key)
        if isinstance(single_value, str) and single_value.strip():
            return [single_value.strip()]

        return list(default_value)
