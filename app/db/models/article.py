from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

LONG_TEXT = Text().with_variant(LONGTEXT(), "mysql")


class Article(TimestampMixin, Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # 文章去重统一依赖 url_hash，避免 MySQL 在长 URL + utf8mb4 下出现唯一索引过长问题。
    canonical_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    crawl_error: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    is_selected_for_daily: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    source: Mapped["Source"] = relationship(back_populates="articles")
    content: Mapped[Optional["ArticleContent"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ArticleContent(TimestampMixin, Base):
    __tablename__ = "article_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, unique=True)
    raw_html: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    clean_content: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    translated_content: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    generated_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    keywords_json: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    ai_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    ai_error: Mapped[Optional[str]] = mapped_column(LONG_TEXT, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    article: Mapped["Article"] = relationship(back_populates="content")


from app.db.models.source import Source  # noqa: E402
