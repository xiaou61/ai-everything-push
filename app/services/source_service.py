from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.source import Source, SourceRule
from app.schemas.source import SourceCreate, SourceUpdate


def list_sources(session: Session) -> list[Source]:
    statement = select(Source).options(selectinload(Source.rules)).order_by(Source.created_at.desc())
    return list(session.scalars(statement).unique())


def create_source(session: Session, payload: SourceCreate) -> Source:
    source = Source(
        name=payload.name,
        slug=payload.slug,
        site_url=str(payload.site_url),
        source_type=payload.source_type,
        feed_url=str(payload.feed_url) if payload.feed_url else None,
        list_url=str(payload.list_url) if payload.list_url else None,
        language_hint=payload.language_hint,
        category=payload.category,
        enabled=payload.enabled,
        include_in_daily=payload.include_in_daily,
        crawl_interval_minutes=payload.crawl_interval_minutes,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def get_source(session: Session, source_id: int) -> Optional[Source]:
    statement = select(Source).options(selectinload(Source.rules)).where(Source.id == source_id).limit(1)
    return session.scalar(statement)


def update_source(session: Session, source: Source, payload: SourceUpdate) -> Source:
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key in {"site_url", "feed_url", "list_url"} and value is not None:
            setattr(source, key, str(value))
        else:
            setattr(source, key, value)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def toggle_source(session: Session, source: Source) -> Source:
    source.enabled = not source.enabled
    session.add(source)
    session.commit()
    session.refresh(source)
    return source
