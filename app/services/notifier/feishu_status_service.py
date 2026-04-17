from __future__ import annotations

from urllib.parse import urlparse

from app.core.config import get_settings


def get_feishu_status() -> dict:
    settings = get_settings()
    webhook_url = (settings.feishu_webhook_url or "").strip()
    configured = bool(webhook_url)

    return {
        "configured": configured,
        "masked_webhook": _mask_webhook_url(webhook_url),
        "site_base_url": settings.site_base_url,
        "message": "已配置 FEISHU_WEBHOOK_URL，可发送测试消息。" if configured else "尚未配置 FEISHU_WEBHOOK_URL。",
    }


def _mask_webhook_url(webhook_url: str) -> str:
    if not webhook_url:
        return ""

    parsed = urlparse(webhook_url)
    if not parsed.scheme or not parsed.netloc:
        return "已配置，但格式无法识别"

    path = parsed.path or "/"
    if len(path) <= 12:
        masked_path = "****"
    else:
        masked_path = f"{path[:8]}...{path[-4:]}"

    return f"{parsed.scheme}://{parsed.netloc}{masked_path}"
