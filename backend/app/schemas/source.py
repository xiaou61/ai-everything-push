from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from app.models.entities import SourceType


class SourceBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    url: HttpUrl
    source_type: SourceType
    category_hint: str | None = Field(default=None, max_length=80)
    parser_config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    fetch_limit: int = Field(default=20, ge=1, le=100)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    url: HttpUrl | None = None
    source_type: SourceType | None = None
    category_hint: str | None = Field(default=None, max_length=80)
    parser_config: dict[str, Any] | None = None
    enabled: bool | None = None
    fetch_limit: int | None = Field(default=None, ge=1, le=100)


class SourceResponse(SourceBase):
    id: int
    last_synced_at: str | None
    created_at: str
    updated_at: str

