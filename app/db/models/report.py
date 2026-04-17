from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DailyReport(TimestampMixin, Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    intro: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft")
    html_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    html_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    article_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    feishu_pushed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    items: Mapped[List["DailyReportItem"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )


class DailyReportItem(Base):
    __tablename__ = "daily_report_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("daily_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    section_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    report: Mapped["DailyReport"] = relationship(back_populates="items")
    article: Mapped["Article"] = relationship()


from app.db.models.article import Article  # noqa: E402

