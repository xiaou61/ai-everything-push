from __future__ import annotations

from datetime import date


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

