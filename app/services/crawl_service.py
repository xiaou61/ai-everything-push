from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.job_run import JobRun
from app.db.models.source import Source
from app.services.article_ingest_service import ArticlePayload, create_or_update_article
from app.services.crawler.content_extractor import extract_text_content
from app.services.crawler.rss_client import FeedEntry, fetch_feed_entries
from app.services.crawler.web_client import WebEntry, extract_article_links, fetch_url_text, parse_headers_json


@dataclass
class CrawlSummary:
    job_id: int
    processed_count: int
    created_count: int
    updated_count: int
    source_count: int
    errors: list[str]


def crawl_enabled_sources(session: Session) -> CrawlSummary:
    job = JobRun(
        job_name="crawl_sources_job",
        trigger_type="manual",
        status="running",
        started_at=datetime.utcnow(),
        processed_count=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    sources = list(
        session.scalars(
            select(Source)
            .options(selectinload(Source.rules))
            .where(Source.enabled.is_(True))
            .order_by(Source.id.asc())
        )
    )
    processed_count = 0
    created_count = 0
    updated_count = 0
    errors: list[str] = []

    for source in sources:
        try:
            entries = _load_entries(source)
            for entry in entries:
                rule = source.rules[0] if source.rules else None
                headers = parse_headers_json(rule.request_headers_json if rule else None)
                html = fetch_url_text(entry.link, headers=headers) if headers else fetch_url_text(entry.link)
                content = extract_text_content(
                    html,
                    content_selector=rule.content_selector if rule else None,
                    remove_selectors=rule.remove_selectors if rule else None,
                )
                _, created = create_or_update_article(
                    session,
                    source,
                    ArticlePayload(
                        title=entry.title,
                        canonical_url=entry.link,
                        author=entry.author,
                        published_at=entry.published_at,
                        language=source.language_hint,
                        raw_html=html,
                        clean_content=content,
                    ),
                )
                processed_count += 1
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{source.name}: {exc}")

    job.status = "success" if not errors else "partial_success"
    job.finished_at = datetime.utcnow()
    job.processed_count = processed_count
    job.error_message = "\n".join(errors) if errors else None
    session.add(job)
    session.commit()

    return CrawlSummary(
        job_id=job.id,
        processed_count=processed_count,
        created_count=created_count,
        updated_count=updated_count,
        source_count=len(sources),
        errors=errors,
    )


def _load_entries(source: Source) -> list[FeedEntry | WebEntry]:
    if source.source_type == "rss" and source.feed_url:
        return fetch_feed_entries(source.feed_url)

    if source.source_type == "web":
        list_url = source.list_url or source.site_url
        rule = source.rules[0] if source.rules else None
        headers = parse_headers_json(rule.request_headers_json if rule else None)
        html = fetch_url_text(list_url, headers=headers) if headers else fetch_url_text(list_url)
        return extract_article_links(
            list_url,
            html,
            list_item_selector=rule.list_item_selector if rule else None,
            link_selector=rule.link_selector if rule else None,
        )

    return []
