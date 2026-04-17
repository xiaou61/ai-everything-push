from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelConfigBase(BaseModel):
    task_type: str = Field(pattern="^(translation|summary|classification|title)$")
    provider_name: str = Field(min_length=1, max_length=64)
    model_name: str = Field(min_length=1, max_length=255)
    base_url: str = Field(min_length=1, max_length=500)
    api_key_env_name: str = Field(min_length=1, max_length=255)
    temperature: str = Field(default="0.2", max_length=32)
    max_tokens: int = Field(default=4000, ge=128, le=32768)
    enabled: bool = True
    is_default: bool = True


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    task_type: Optional[str] = Field(default=None, pattern="^(translation|summary|classification|title)$")
    provider_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    model_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    base_url: Optional[str] = Field(default=None, min_length=1, max_length=500)
    api_key_env_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    temperature: Optional[str] = Field(default=None, max_length=32)
    max_tokens: Optional[int] = Field(default=None, ge=128, le=32768)
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None


class ModelConfigRead(ModelConfigBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
