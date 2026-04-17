from __future__ import annotations

from pydantic import BaseModel, Field


class FeishuStatusRead(BaseModel):
    configured: bool
    masked_webhook: str
    site_base_url: str
    message: str


class FeishuTestSendRequest(BaseModel):
    title: str = Field(default="技术论坛日报联调消息", min_length=1, max_length=100)
    message: str = Field(default="这是一条来自后台的飞书测试消息。", min_length=1, max_length=500)


class FeishuTestSendResult(BaseModel):
    status: str
    message: str
    detail: str = ""
