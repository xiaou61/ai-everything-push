from __future__ import annotations

from datetime import datetime

import httpx

from app.core.config import Settings, get_settings
from app.models.entities import DailyDigest


class FeishuService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def build_message_payload(self, digest: DailyDigest) -> dict:
        lines = [[{"tag": "text", "text": digest.overview}]]
        detail_url = f"{self.settings.daily_digest_site_base_url.rstrip('/')}/reports/{digest.digest_date.isoformat()}"
        lines.append([{"tag": "a", "text": "查看完整日报", "href": detail_url}])

        for section in digest.sections[:4]:
            lines.append([{"tag": "text", "text": f"{section['category']} ({section['count']})"}])
            for article in section["articles"][:3]:
                lines.append(
                    [
                        {"tag": "a", "text": article["title"], "href": article["url"]},
                        {"tag": "text", "text": f" - {article['summary']}"},
                    ]
                )

        return {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": digest.headline,
                        "content": lines,
                    }
                }
            },
        }

    def push_digest(self, digest: DailyDigest) -> None:
        if not self.settings.feishu_webhook_url:
            raise ValueError("FEISHU_WEBHOOK_URL 未配置，无法推送飞书。")

        payload = self.build_message_payload(digest)
        response = httpx.post(
            self.settings.feishu_webhook_url,
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        digest.pushed_at = datetime.utcnow()

