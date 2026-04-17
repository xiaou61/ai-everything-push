from __future__ import annotations

from datetime import date, datetime

from app.core.database import SessionLocal
from app.db.models import Article, ArticleContent, DailyReport, DailyReportItem


def test_get_report_detail_api(client):
    report_id = _build_report_fixture()

    response = client.get(f"/admin/api/reports/{report_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "原始日报标题"
    assert len(payload["items"]) == 2
    assert payload["items"][0]["display_order"] == 1
    assert len(payload["candidate_articles"]) == 1
    assert payload["candidate_articles"][0]["generated_title"] == "候选标题 C"


def test_update_report_detail_api(client):
    report_id = _build_report_fixture()

    original = client.get(f"/admin/api/reports/{report_id}").json()
    first_item = original["items"][0]
    second_item = original["items"][1]

    response = client.put(
        f"/admin/api/reports/{report_id}",
        json={
            "title": "编辑后的日报标题",
            "intro": "编辑后的导语",
            "items": [
                {
                    "id": second_item["id"],
                    "article_id": second_item["article_id"],
                    "display_order": 1,
                    "section_name": "精选速读",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "编辑后的日报标题"
    assert payload["intro"] == "编辑后的导语"
    assert payload["article_count"] == 1
    assert payload["items"][0]["id"] == second_item["id"]
    assert payload["items"][0]["section_name"] == "精选速读"

    session = SessionLocal()
    try:
        report = session.get(DailyReport, report_id)
        assert report is not None
        assert report.article_count == 1
        assert session.query(DailyReportItem).filter(DailyReportItem.report_id == report_id).count() == 1
        assert session.query(DailyReportItem).filter(DailyReportItem.id == first_item["id"]).count() == 0
    finally:
        session.close()


def test_publish_report_updates_public_html(client):
    report_id = _build_report_fixture()
    original = client.get(f"/admin/api/reports/{report_id}").json()

    update_response = client.put(
        f"/admin/api/reports/{report_id}",
        json={
            "title": "新的日报标题",
            "intro": "新的日报导语",
            "items": [
                {
                    "id": original["items"][0]["id"],
                    "article_id": original["items"][0]["article_id"],
                    "display_order": 1,
                    "section_name": "编辑后栏目",
                },
                {
                    "id": original["items"][1]["id"],
                    "article_id": original["items"][1]["article_id"],
                    "display_order": 2,
                    "section_name": "编辑后栏目",
                },
            ],
        },
    )
    assert update_response.status_code == 200

    publish_response = client.post(f"/admin/api/reports/{report_id}/publish")
    assert publish_response.status_code == 200
    payload = publish_response.json()
    assert "/daily/" in payload["html_url"]

    public_page = client.get("/daily/2026-04-17")
    assert public_page.status_code == 200
    assert "新的日报标题" in public_page.text
    assert "新的日报导语" in public_page.text
    assert "编辑后栏目" in public_page.text


def test_update_report_can_add_candidate_article(client):
    report_id = _build_report_fixture()
    original = client.get(f"/admin/api/reports/{report_id}").json()
    candidate = original["candidate_articles"][0]

    response = client.put(
        f"/admin/api/reports/{report_id}",
        json={
            "title": original["title"],
            "intro": original["intro"],
            "items": [
                {
                    "id": item["id"],
                    "article_id": item["article_id"],
                    "display_order": index + 1,
                    "section_name": item["section_name"],
                }
                for index, item in enumerate(original["items"])
            ]
            + [
                {
                    "id": None,
                    "article_id": candidate["article_id"],
                    "display_order": 3,
                    "section_name": "人工补充",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["article_count"] == 3
    assert any(item["article_id"] == candidate["article_id"] for item in payload["items"])
    assert all(item["article_id"] != candidate["article_id"] for item in payload["candidate_articles"])


def _build_report_fixture() -> int:
    session = SessionLocal()
    try:
        source_response = {
            "id": None,
        }
        if source_response["id"] is None:
            from app.db.models import Source

            source = Source(
                name="日报编辑来源",
                slug="report-editor-source",
                source_type="web",
                site_url="https://example.com",
                list_url="https://example.com/blog",
            )
            session.add(source)
            session.flush()
            source_id = source.id
        else:
            source_id = source_response["id"]

        article_a = Article(
            source_id=source_id,
            title="文章 A",
            canonical_url="https://example.com/articles/a",
            language="zh",
            published_at=datetime(2026, 4, 17, 9, 0, 0),
            url_hash="report-editor-a",
            status="processed",
        )
        article_b = Article(
            source_id=source_id,
            title="文章 B",
            canonical_url="https://example.com/articles/b",
            language="zh",
            published_at=datetime(2026, 4, 17, 10, 0, 0),
            url_hash="report-editor-b",
            status="processed",
        )
        article_c = Article(
            source_id=source_id,
            title="文章 C",
            canonical_url="https://example.com/articles/c",
            language="zh",
            published_at=datetime(2026, 4, 17, 11, 0, 0),
            url_hash="report-editor-c",
            status="processed",
        )
        session.add_all([article_a, article_b, article_c])
        session.flush()
        session.add_all(
            [
                ArticleContent(
                    article_id=article_a.id,
                    clean_content="正文 A",
                    summary="摘要 A",
                    category="技术观察",
                    generated_title="生成标题 A",
                    ai_status="success",
                ),
                ArticleContent(
                    article_id=article_b.id,
                    clean_content="正文 B",
                    summary="摘要 B",
                    category="架构实践",
                    generated_title="生成标题 B",
                    ai_status="success",
                ),
                ArticleContent(
                    article_id=article_c.id,
                    clean_content="正文 C",
                    summary="摘要 C",
                    category="技术观察",
                    generated_title="候选标题 C",
                    ai_status="success",
                ),
            ]
        )

        report = DailyReport(
            report_date=date(2026, 4, 17),
            title="原始日报标题",
            intro="原始日报导语",
            status="published",
            source_count=1,
            article_count=2,
            html_url="/daily/2026-04-17",
            feishu_pushed=False,
        )
        session.add(report)
        session.flush()
        session.add_all(
            [
                DailyReportItem(report_id=report.id, article_id=article_a.id, display_order=1, section_name="技术观察"),
                DailyReportItem(report_id=report.id, article_id=article_b.id, display_order=2, section_name="架构实践"),
            ]
        )
        session.commit()
        return report.id
    finally:
        session.close()
