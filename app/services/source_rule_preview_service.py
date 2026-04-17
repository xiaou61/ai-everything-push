from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.db.models.source import Source
from app.schemas.source_rule import SourceRuleUpsert
from app.services.crawler.content_extractor import extract_text_content
from app.services.crawler.rss_client import fetch_feed_entries
from app.services.crawler.web_client import extract_article_links, fetch_url_text, parse_headers_json


@dataclass
class RulePreviewResult:
    mode: str
    source_type: str
    request_url: str
    article_url: Optional[str] = None
    items: Optional[list[dict]] = None
    extracted_text: Optional[str] = None
    extracted_length: int = 0


def preview_source_rule(
    source: Source,
    rule: SourceRuleUpsert,
    preview_mode: str,
    preview_url: Optional[str] = None,
) -> RulePreviewResult:
    normalized_mode = preview_mode if preview_mode in {"list", "article"} else "list"
    headers = parse_headers_json(rule.request_headers_json)

    if source.source_type == "rss":
        return _preview_rss_source(source, rule, normalized_mode, preview_url)

    return _preview_web_source(source, rule, normalized_mode, preview_url, headers)


def _preview_rss_source(
    source: Source,
    rule: SourceRuleUpsert,
    preview_mode: str,
    preview_url: Optional[str],
) -> RulePreviewResult:
    feed_url = preview_url or source.feed_url or source.site_url
    entries = fetch_feed_entries(feed_url)
    if preview_mode == "list":
        items = [{"title": item.title, "link": item.link} for item in entries[:10]]
        return RulePreviewResult(
            mode="list",
            source_type="rss",
            request_url=feed_url,
            items=items,
        )

    article_url = preview_url if preview_url and preview_url != feed_url else (entries[0].link if entries else "")
    if not article_url:
        return RulePreviewResult(
            mode="article",
            source_type="rss",
            request_url=feed_url,
            article_url="",
            extracted_text="",
            extracted_length=0,
        )
    html = fetch_url_text(article_url) if article_url else ""
    extracted = extract_text_content(
        html,
        content_selector=rule.content_selector,
        remove_selectors=rule.remove_selectors,
    )
    return RulePreviewResult(
        mode="article",
        source_type="rss",
        request_url=feed_url,
        article_url=article_url,
        extracted_text=extracted[:4000],
        extracted_length=len(extracted),
    )


def _preview_web_source(
    source: Source,
    rule: SourceRuleUpsert,
    preview_mode: str,
    preview_url: Optional[str],
    headers: Optional[dict],
) -> RulePreviewResult:
    list_url = source.list_url or source.site_url
    request_url = preview_url or list_url

    if preview_mode == "list":
        html = fetch_url_text(request_url, headers=headers) if headers else fetch_url_text(request_url)
        items = extract_article_links(
            request_url,
            html,
            list_item_selector=rule.list_item_selector,
            link_selector=rule.link_selector,
        )
        return RulePreviewResult(
            mode="list",
            source_type="web",
            request_url=request_url,
            items=[{"title": item.title, "link": item.link} for item in items[:10]],
        )

    article_url = preview_url
    if not article_url:
        html = fetch_url_text(list_url, headers=headers) if headers else fetch_url_text(list_url)
        items = extract_article_links(
            list_url,
            html,
            list_item_selector=rule.list_item_selector,
            link_selector=rule.link_selector,
        )
        article_url = items[0].link if items else ""
    if not article_url:
        return RulePreviewResult(
            mode="article",
            source_type="web",
            request_url=list_url,
            article_url="",
            extracted_text="",
            extracted_length=0,
        )

    html = fetch_url_text(article_url, headers=headers) if headers else fetch_url_text(article_url)
    extracted = extract_text_content(
        html,
        content_selector=rule.content_selector,
        remove_selectors=rule.remove_selectors,
    )
    return RulePreviewResult(
        mode="article",
        source_type="web",
        request_url=article_url,
        article_url=article_url,
        extracted_text=extracted[:4000],
        extracted_length=len(extracted),
    )
