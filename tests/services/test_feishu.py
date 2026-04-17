from __future__ import annotations

from app.services.notifier.feishu import build_report_payload


def test_build_feishu_payload():
    payload = build_report_payload(
        title="技术日报",
        highlights=["A", "B", "C"],
        url="http://localhost:8000/daily/2026-04-17",
        article_count=3,
    )
    assert payload["msg_type"] == "post"
    assert payload["content"]["post"]["zh_cn"]["title"] == "技术日报"
