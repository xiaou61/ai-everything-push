from __future__ import annotations

from datetime import date, datetime

from app.core.database import SessionLocal
from app.db.models import Article, ArticleContent, DailyReport, JobRun


def test_dashboard_data_api(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "仪表盘来源",
            "slug": "dashboard-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
        },
    )
    assert source_response.status_code == 201

    session = SessionLocal()
    try:
        session.add(
            JobRun(
                job_name="crawl_sources_job",
                trigger_type="manual",
                status="success",
                started_at=datetime(2026, 4, 17, 9, 0, 0),
                finished_at=datetime(2026, 4, 17, 9, 1, 0),
                processed_count=5,
            )
        )
        session.commit()
    finally:
        session.close()

    response = client.get("/admin/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["stats"]["source_count"] == 1
    assert payload["stats"]["job_count"] == 1
    assert len(payload["recent_jobs"]) == 1
    assert "running" in payload["scheduler_status"]


def test_admin_collections_api(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "集合来源",
            "slug": "collection-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
        },
    )
    source_id = source_response.json()["id"]

    session = SessionLocal()
    try:
        article = Article(
            source_id=source_id,
            title="示例文章",
            canonical_url="https://example.com/articles/demo",
            language="zh",
            url_hash="hash-demo-1",
            status="processed",
        )
        session.add(article)
        session.flush()
        session.add(
            ArticleContent(
                article_id=article.id,
                clean_content="正文内容",
                summary="摘要内容",
                category="AI 工程",
                generated_title="生成标题",
                ai_status="success",
            )
        )
        session.add(
            DailyReport(
                report_date=date(2026, 4, 17),
                title="日报标题",
                intro="日报导语",
                status="published",
                html_url="/daily/2026-04-17",
                source_count=1,
                article_count=1,
                feishu_pushed=True,
            )
        )
        session.add(
            JobRun(
                job_name="report_generation_job",
                trigger_type="manual",
                status="success",
                started_at=datetime(2026, 4, 17, 18, 0, 0),
                finished_at=datetime(2026, 4, 17, 18, 2, 0),
                processed_count=1,
            )
        )
        session.commit()
    finally:
        session.close()

    articles_response = client.get("/admin/api/articles")
    reports_response = client.get("/admin/api/reports")
    jobs_response = client.get("/admin/api/jobs")
    scheduler_response = client.get("/admin/api/scheduler/status")

    assert articles_response.status_code == 200
    assert reports_response.status_code == 200
    assert jobs_response.status_code == 200
    assert scheduler_response.status_code == 200

    assert articles_response.json()[0]["generated_title"] == "生成标题"
    assert reports_response.json()[0]["title"] == "日报标题"
    assert jobs_response.json()[0]["job_name"] == "report_generation_job"
    assert "available" in scheduler_response.json()
