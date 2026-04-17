from __future__ import annotations

from datetime import date

from app.services.job_service import JobAlreadyRunningError


def test_process_and_report_flow(client, monkeypatch):
    client.post(
        "/admin/api/sources",
        json={
            "name": "Test RSS",
            "slug": "test-rss-report",
            "source_type": "rss",
            "site_url": "https://example.com",
            "feed_url": "https://example.com/feed.xml",
            "language_hint": "zh",
        },
    )

    monkeypatch.setattr(
        "app.services.crawl_service.fetch_feed_entries",
        lambda _: [],
    )

    from app.core.database import SessionLocal
    from app.db.models.source import Source
    from app.services.article_ingest_service import ArticlePayload, create_or_update_article

    session = SessionLocal()
    try:
        source = session.query(Source).filter(Source.slug == "test-rss-report").one()
        create_or_update_article(
            session,
            source,
            ArticlePayload(
                title="美团网关演进",
                canonical_url="https://example.com/post-1",
                clean_content="这篇文章介绍了网关架构演进、流量治理与平台能力建设。",
                language="zh",
            ),
        )
    finally:
        session.close()

    process_response = client.post("/admin/api/jobs/process/run")
    assert process_response.status_code == 200
    assert process_response.json()["success_count"] == 1

    report_response = client.post(f"/admin/api/jobs/report/run?report_date={date.today().isoformat()}")
    assert report_response.status_code == 200
    html_url = report_response.json()["html_url"]
    assert "/daily/" in html_url

    public_page = client.get(f"/daily/{date.today().isoformat()}")
    assert public_page.status_code == 200
    assert "技术日报" in public_page.text
    assert "今天看点" in public_page.text
    assert "阅读导航" in public_page.text


def test_run_process_job_returns_409_when_job_conflicts(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.jobs.process_pending_articles",
        lambda session: (_ for _ in ()).throw(JobAlreadyRunningError("process_articles_job 正在运行中，请稍后再试")),
    )

    response = client.post("/admin/api/jobs/process/run")
    assert response.status_code == 409
    assert "正在运行中" in response.json()["detail"]


def test_run_report_job_returns_409_when_job_conflicts(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.jobs.generate_daily_report",
        lambda session, report_date=None: (_ for _ in ()).throw(JobAlreadyRunningError("generate_report_job 正在运行中，请稍后再试")),
    )

    response = client.post(f"/admin/api/jobs/report/run?report_date={date.today().isoformat()}")
    assert response.status_code == 409
    assert "正在运行中" in response.json()["detail"]


def test_run_push_job_returns_409_when_job_conflicts(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.jobs.push_report_to_feishu",
        lambda session, report_date: (_ for _ in ()).throw(JobAlreadyRunningError("push_report_job 正在运行中，请稍后再试")),
    )

    response = client.post(f"/admin/api/jobs/push/run?report_date={date.today().isoformat()}")
    assert response.status_code == 409
    assert "正在运行中" in response.json()["detail"]
