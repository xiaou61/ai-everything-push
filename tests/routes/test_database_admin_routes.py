from __future__ import annotations

from datetime import date, datetime, timedelta

from app.core.database import SessionLocal
from app.db.models import Article, ArticleContent, DailyReport, DailyReportItem, JobRun


def test_database_overview_api(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "数据库概览来源",
            "slug": "database-overview-source",
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
            title="数据库概览文章",
            canonical_url="https://example.com/articles/database-overview",
            url_hash="database-overview-1",
            status="crawled",
        )
        session.add(article)
        session.flush()
        session.add(
            ArticleContent(
                article_id=article.id,
                clean_content="正文",
                ai_status="failed",
                ai_error="模型超时",
            )
        )
        session.add(
            JobRun(
                job_name="crawl_sources_job",
                trigger_type="manual",
                status="success",
                started_at=datetime(2026, 4, 17, 9, 0, 0),
                finished_at=datetime(2026, 4, 17, 9, 5, 0),
                processed_count=3,
            )
        )
        session.add(
            DailyReport(
                report_date=date(2026, 4, 17),
                title="数据库概览日报",
                status="published",
                source_count=1,
                article_count=1,
                feishu_pushed=False,
            )
        )
        session.commit()
    finally:
        session.close()

    response = client.get("/admin/api/database/overview")
    assert response.status_code == 200

    payload = response.json()
    assert payload["connection"]["dialect"] == "sqlite"
    assert payload["metrics"]["article_count"] == 1
    assert payload["metrics"]["report_count"] == 1
    assert payload["metrics"]["job_run_count"] == 1
    assert any(item["key"] == "articles" and item["count"] == 1 for item in payload["tables"])
    assert any(item["key"] == "ai_failed" and item["count"] == 1 for item in payload["article_status_breakdown"])


def test_cleanup_old_job_runs_api(client):
    session = SessionLocal()
    try:
        session.add_all(
            [
                JobRun(
                    job_name="old_job",
                    trigger_type="scheduler",
                    status="success",
                    started_at=datetime.utcnow() - timedelta(days=10, minutes=5),
                    finished_at=datetime.utcnow() - timedelta(days=10),
                    processed_count=1,
                ),
                JobRun(
                    job_name="recent_job",
                    trigger_type="manual",
                    status="success",
                    started_at=datetime.utcnow() - timedelta(days=1, minutes=5),
                    finished_at=datetime.utcnow() - timedelta(days=1),
                    processed_count=1,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    response = client.post("/admin/api/database/maintenance/jobs/cleanup", json={"keep_days": 7})
    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1

    jobs_response = client.get("/admin/api/jobs")
    assert jobs_response.status_code == 200
    assert len(jobs_response.json()) == 1
    assert jobs_response.json()[0]["job_name"] == "recent_job"


def test_cleanup_failed_articles_api(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "失败文章来源",
            "slug": "failed-article-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
        },
    )
    source_id = source_response.json()["id"]

    session = SessionLocal()
    try:
        failed_article = Article(
            source_id=source_id,
            title="失败文章",
            canonical_url="https://example.com/articles/failed",
            url_hash="failed-article-1",
            status="crawled",
        )
        success_article = Article(
            source_id=source_id,
            title="成功文章",
            canonical_url="https://example.com/articles/success",
            url_hash="success-article-1",
            status="crawled",
        )
        session.add_all([failed_article, success_article])
        session.flush()
        session.add_all(
            [
                ArticleContent(
                    article_id=failed_article.id,
                    clean_content="失败正文",
                    ai_status="failed",
                    ai_error="翻译失败",
                ),
                ArticleContent(
                    article_id=success_article.id,
                    clean_content="成功正文",
                    ai_status="success",
                    summary="已处理",
                ),
            ]
        )
        report = DailyReport(
            report_date=date(2026, 4, 17),
            title="日报",
            status="published",
            source_count=1,
            article_count=2,
            feishu_pushed=False,
        )
        session.add(report)
        session.flush()
        session.add_all(
            [
                DailyReportItem(report_id=report.id, article_id=failed_article.id, display_order=1, section_name="异常"),
                DailyReportItem(report_id=report.id, article_id=success_article.id, display_order=2, section_name="正常"),
            ]
        )
        session.commit()
    finally:
        session.close()

    response = client.post("/admin/api/database/maintenance/articles/failed/cleanup")
    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1

    session = SessionLocal()
    try:
        assert session.query(Article).count() == 1
        assert session.query(ArticleContent).count() == 1
        remaining_item = session.query(DailyReportItem).one()
        assert remaining_item.section_name == "正常"
    finally:
        session.close()


def test_delete_report_api(client, tmp_path):
    session = SessionLocal()
    try:
        html_path = tmp_path / "2026-04-17.html"
        html_path.write_text("<html>日报</html>", encoding="utf-8")
        report = DailyReport(
            report_date=date(2026, 4, 17),
            title="待删除日报",
            status="published",
            html_path=str(html_path),
            html_url="/daily/2026-04-17",
            source_count=0,
            article_count=0,
            feishu_pushed=False,
        )
        session.add(report)
        session.commit()
        session.refresh(report)
        report_id = report.id
    finally:
        session.close()

    response = client.delete(f"/admin/api/database/reports/{report_id}")
    assert response.status_code == 200
    assert response.json()["removed_html"] is True
    assert not html_path.exists()

    reports_response = client.get("/admin/api/reports")
    assert reports_response.status_code == 200
    assert reports_response.json() == []
