from __future__ import annotations

from datetime import date

from app.core.config import Settings
from app.core.database import SessionLocal
from app.db.models import DailyReport, DailyReportItem, JobRun, Source, Article, ArticleContent
from app.services.notifier.feishu import (
    build_report_payload,
    build_text_payload,
    push_report_to_feishu,
    render_feishu_template,
)
from app.services.system_setting_service import upsert_many


def test_build_feishu_payload():
    payload = build_report_payload(title="技术日报", body="第一行\n第二行")
    assert payload["msg_type"] == "post"
    assert payload["content"]["post"]["zh_cn"]["title"] == "技术日报"
    assert payload["content"]["post"]["zh_cn"]["content"][0][0]["text"] == "第一行"


def test_build_feishu_text_payload():
    payload = build_text_payload(title="联调标题", message="联调消息")
    assert payload["msg_type"] == "post"
    assert payload["content"]["post"]["zh_cn"]["title"] == "联调标题"


def test_render_feishu_template():
    rendered = render_feishu_template(
        "日报：{{report_date}} {{report_title}} {{unknown}}",
        {
            "report_date": "2026-04-17",
            "report_title": "技术日报",
        },
    )
    assert rendered == "日报：2026-04-17 技术日报 {{unknown}}"


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


def test_push_report_to_feishu_uses_template_settings(monkeypatch):
    captured_payload: dict = {}
    session = SessionLocal()
    try:
        source = Source(
            name="推送来源",
            slug="push-source",
            site_url="https://example.com",
            source_type="web",
            list_url="https://example.com/blog",
        )
        session.add(source)
        session.flush()

        article = Article(
            source_id=source.id,
            title="原始标题",
            canonical_url="https://example.com/articles/1",
            language="zh",
            url_hash="push-template-1",
            status="processed",
        )
        session.add(article)
        session.flush()
        session.add(
            ArticleContent(
                article_id=article.id,
                clean_content="正文",
                summary="摘要",
                category="技术观察",
                generated_title="今日亮点文章",
                ai_status="success",
            )
        )
        report = DailyReport(
            report_date=date(2026, 4, 17),
            title="编辑后的日报标题",
            intro="这是日报导语",
            status="published",
            html_url="http://127.0.0.1:8000/daily/2026-04-17",
            source_count=1,
            article_count=1,
            feishu_pushed=False,
        )
        session.add(report)
        session.flush()
        session.add(
            DailyReportItem(
                report_id=report.id,
                article_id=article.id,
                display_order=1,
                section_name="精选",
            )
        )
        upsert_many(
            session,
            [
                {
                    "setting_key": "feishu.report_title_template",
                    "setting_value": "日报：{{report_date}}",
                    "description": "飞书日报推送标题模板",
                },
                {
                    "setting_key": "feishu.report_body_template",
                    "setting_value": "标题：{{report_title}}\n导语：{{report_intro}}\n{{highlights_bullets}}\n链接：{{report_url}}",
                    "description": "飞书日报推送正文模板",
                },
            ],
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

    def fake_send_feishu_payload(webhook_url, payload):
        captured_payload.update(payload)
        return {"code": 0}

    monkeypatch.setattr("app.services.notifier.feishu.send_feishu_payload", fake_send_feishu_payload)

    session = SessionLocal()
    try:
        result = push_report_to_feishu(session, date(2026, 4, 17))
        assert result["status"] == "success"
    finally:
        session.close()

    assert captured_payload["content"]["post"]["zh_cn"]["title"] == "日报：2026-04-17"
    content_lines = [row[0]["text"] for row in captured_payload["content"]["post"]["zh_cn"]["content"]]
    assert "标题：编辑后的日报标题" in content_lines
    assert "导语：这是日报导语" in content_lines
    assert "• 今日亮点文章" in content_lines


def test_push_report_to_feishu_skips_duplicate_scheduler_push(monkeypatch):
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
                feishu_pushed=True,
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

    called = {"count": 0}

    def fake_send_feishu_payload(webhook_url, payload):
        called["count"] += 1
        return {"code": 0}

    monkeypatch.setattr("app.services.notifier.feishu.send_feishu_payload", fake_send_feishu_payload)

    session = SessionLocal()
    try:
        result = push_report_to_feishu(session, date(2026, 4, 17), trigger_type="scheduler")
        assert result["status"] == "skipped"
        assert result["message"] == "日报已推送，跳过重复调度"

        latest_job = session.query(JobRun).order_by(JobRun.id.desc()).first()
        assert latest_job is not None
        assert latest_job.status == "skipped"
    finally:
        session.close()

    assert called["count"] == 0
