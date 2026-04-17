from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Article(TimestampMixin, Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    crawl_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    raw_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clean_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translated_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    generated_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    keywords_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    ai_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    article: Mapped["Article"] = relationship(back_populates="content")


from app.db.models.source import Source  # noqa: E402

