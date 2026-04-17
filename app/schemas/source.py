from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    site_url: HttpUrl
    source_type: str = Field(pattern="^(rss|web)$")
    feed_url: Optional[HttpUrl] = None
    list_url: Optional[HttpUrl] = None
    language_hint: Optional[str] = Field(default=None, max_length=32)
    category: Optional[str] = Field(default=None, max_length=100)
    enabled: bool = True
    include_in_daily: bool = True
    crawl_interval_minutes: int = Field(default=60, ge=5, le=1440)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    site_url: Optional[HttpUrl] = None
    source_type: Optional[str] = Field(default=None, pattern="^(rss|web)$")
    feed_url: Optional[HttpUrl] = None
    list_url: Optional[HttpUrl] = None
    language_hint: Optional[str] = Field(default=None, max_length=32)
    category: Optional[str] = Field(default=None, max_length=100)
    enabled: Optional[bool] = None
    include_in_daily: Optional[bool] = None
    crawl_interval_minutes: Optional[int] = Field(default=None, ge=5, le=1440)


class SourceRead(SourceBase):
    id: int
    last_crawled_at: Optional[datetime] = None
    last_crawl_status: Optional[str] = None
    consecutive_failures: int = 0
    last_crawl_error: Optional[str] = None
    last_crawl_processed_count: int = 0

    model_config = ConfigDict(from_attributes=True)
