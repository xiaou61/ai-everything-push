from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SystemSettingUpsert(BaseModel):
    setting_key: str = Field(min_length=1, max_length=255)
    setting_value: str = Field(min_length=0)
    description: str = Field(default="", max_length=1000)


class SystemSettingRead(SystemSettingUpsert):
    id: int

    model_config = ConfigDict(from_attributes=True)

