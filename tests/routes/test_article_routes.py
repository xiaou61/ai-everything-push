from __future__ import annotations

from app.core.database import SessionLocal
from app.db.models import Article, ArticleContent


def test_get_article_detail_api(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "详情来源",
            "slug": "detail-source",
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
            title="详情文章",
            canonical_url="https://example.com/articles/detail",
            language="zh",
            url_hash="detail-hash-1",
            status="processed",
        )
        session.add(article)
        session.flush()
        session.add(
            ArticleContent(
                article_id=article.id,
                clean_content="正文内容",
                translated_content="正文内容",
                summary="摘要内容",
                category="工程实践",
                generated_title="生成标题",
                ai_status="success",
            )
        )
        session.commit()
        article_id = article.id
    finally:
        session.close()

    response = client.get(f"/admin/api/articles/{article_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == article_id
    assert payload["generated_title"] == "生成标题"
    assert payload["clean_content"] == "正文内容"
    assert payload["ai_status"] == "success"


def test_reprocess_article_api(client, monkeypatch):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "重处理来源",
            "slug": "reprocess-source",
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
            title="Need Reprocess",
            canonical_url="https://example.com/articles/reprocess",
            language="en",
            url_hash="reprocess-hash-1",
            status="failed",
        )
        session.add(article)
        session.flush()
        session.add(
            ArticleContent(
                article_id=article.id,
                clean_content="English body",
                ai_status="failed",
                ai_error="old error",
            )
        )
        session.commit()
        article_id = article.id
    finally:
        session.close()

    monkeypatch.setattr("app.services.article_processing_service.detect_language", lambda _: "en")
    monkeypatch.setattr(
        "app.services.article_processing_service.translate_content",
        lambda session, title, content: "中文译文",
    )
    monkeypatch.setattr(
        "app.services.article_processing_service.summarize_content",
        lambda session, title, content: {"summary": "新的摘要", "highlights": ["A", "B"]},
    )
    monkeypatch.setattr(
        "app.services.article_processing_service.classify_content",
        lambda session, title, content: "AI 工程",
    )
    monkeypatch.setattr(
        "app.services.article_processing_service.generate_display_title",
        lambda session, title, summary: "新的标题",
    )

    response = client.post(f"/admin/api/articles/{article_id}/reprocess")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "processed"
    assert payload["ai_status"] == "success"
    assert payload["article"]["translated_content"] == "中文译文"
    assert payload["article"]["generated_title"] == "新的标题"
    assert payload["article"]["summary"] == "新的摘要"
