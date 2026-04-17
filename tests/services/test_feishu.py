from __future__ import annotations

from datetime import date

from app.core.config import Settings
from app.core.database import SessionLocal
from app.db.models import DailyReport, JobRun
from app.services.notifier.feishu import build_report_payload, build_text_payload, push_report_to_feishu


def test_build_feishu_payload():
    payload = build_report_payload(
        title="技术日报",
        highlights=["A", "B", "C"],
        url="http://localhost:8000/daily/2026-04-17",
        article_count=3,
    )
    assert payload["msg_type"] == "post"
    assert payload["content"]["post"]["zh_cn"]["title"] == "技术日报"


def test_build_feishu_text_payload():
    payload = build_text_payload(title="联调标题", message="联调消息")
    assert payload["msg_type"] == "post"
    assert payload["content"]["post"]["zh_cn"]["title"] == "联调标题"


def test_push_report_to_feishu_marks_failed_when_request_errors(monkeypatch):
    session = SessionLocal()
    try:
        session.add(
            DailyReport(
                report_date=date(2026, 4, 17),
                title="技术日报",
                intro="日报导语",
                status="published",
                html_url="http://127.0.0.1:8000/daily/2026-04-17",
                source_count=1,
                article_count=3,
                feishu_pushed=False,
            )
        )
        session.commit()
    finally:
        session.close()

    monkeypatch.setattr(
        "app.services.notifier.feishu.get_settings",
        lambda: Settings(
            feishu_webhook_url="https://open.feishu.cn/fake-webhook",
            site_base_url="http://127.0.0.1:8000",
        ),
    )
    monkeypatch.setattr(
        "app.services.notifier.feishu.send_feishu_payload",
        lambda webhook_url, payload: (_ for _ in ()).throw(ValueError("飞书接口不可用")),
    )

    session = SessionLocal()
    try:
        result = push_report_to_feishu(session, date(2026, 4, 17))
        assert result["status"] == "failed"
        assert "飞书接口不可用" in result["detail"]

        latest_job = session.query(JobRun).order_by(JobRun.id.desc()).first()
        assert latest_job is not None
        assert latest_job.status == "failed"
        assert latest_job.error_message == "飞书接口不可用"
    finally:
        session.close()
