from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.article import Article, ArticleContent
from app.db.models.source import Source


@dataclass
class ArticlePayload:
    title: str
    canonical_url: str
    author: Optional[str] = None
    published_at: Optional[object] = None
    language: Optional[str] = None
    raw_html: Optional[str] = None
    clean_content: Optional[str] = None


def build_url_hash(url: str) -> str:
    return sha256(url.strip().encode("utf-8")).hexdigest()


def create_or_update_article(session: Session, source: Source, payload: ArticlePayload) -> tuple[Article, bool]:
    url_hash = build_url_hash(payload.canonical_url)
    article = session.scalar(select(Article).where(Article.url_hash == url_hash))
    created = article is None

    if article is None:
        article = Article(
            source_id=source.id,
            title=payload.title,
            canonical_url=payload.canonical_url,
            author=payload.author,
            published_at=payload.published_at,
            language=payload.language,
            url_hash=url_hash,
            status="crawled" if payload.clean_content else "pending",
            is_selected_for_daily=False,
        )
        session.add(article)
        session.flush()
    else:
        article.title = payload.title or article.title
        article.author = payload.author or article.author
        article.published_at = payload.published_at or article.published_at
        article.language = payload.language or article.language
        if payload.clean_content:
            article.status = "crawled"
        session.add(article)

    if payload.raw_html or payload.clean_content:
        content = session.scalar(select(ArticleContent).where(ArticleContent.article_id == article.id))
        if content is None:
            content = ArticleContent(article_id=article.id)
        content.raw_html = payload.raw_html
        content.raw_content = payload.clean_content
        content.clean_content = payload.clean_content
        session.add(content)

    session.commit()
    session.refresh(article)
    return article, created

