from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceRuleBase(BaseModel):
    list_item_selector: Optional[str] = Field(default=None, max_length=255)
    link_selector: Optional[str] = Field(default=None, max_length=255)
    title_selector: Optional[str] = Field(default=None, max_length=255)
    published_at_selector: Optional[str] = Field(default=None, max_length=255)
    author_selector: Optional[str] = Field(default=None, max_length=255)
    content_selector: Optional[str] = Field(default=None, max_length=255)
    remove_selectors: Optional[str] = None
    request_headers_json: Optional[str] = None


class SourceRuleUpsert(SourceRuleBase):
    pass


class SourceRuleRead(SourceRuleBase):
    id: int
    source_id: int

    model_config = ConfigDict(from_attributes=True)

