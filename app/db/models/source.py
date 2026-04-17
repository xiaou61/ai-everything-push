from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    site_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    feed_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    list_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    language_hint: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    include_in_daily: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    crawl_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60, server_default="60")
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_crawl_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_crawl_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_crawl_processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    rules: Mapped[List["SourceRule"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )
    articles: Mapped[List["Article"]] = relationship(back_populates="source")


class SourceRule(TimestampMixin, Base):
    __tablename__ = "source_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    list_item_selector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    link_selector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title_selector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at_selector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_selector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_selector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remove_selectors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_headers_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped["Source"] = relationship(back_populates="rules")


from app.db.models.article import Article  # noqa: E402
