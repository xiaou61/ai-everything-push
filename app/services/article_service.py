from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models.article import Article


def list_articles(session: Session, limit: int = 100) -> list[Article]:
    statement = (
        select(Article)
        .options(joinedload(Article.source), joinedload(Article.content))
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement).unique())


def get_article(session: Session, article_id: int) -> Article | None:
    statement = (
        select(Article)
        .options(joinedload(Article.source), joinedload(Article.content))
        .where(Article.id == article_id)
        .limit(1)
    )
    return session.scalar(statement)
