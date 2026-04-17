from __future__ import annotations

from app.services.crawler.rss_client import FeedEntry


def test_run_crawl_job(client, monkeypatch):
    client.post(
        "/admin/api/sources",
        json={
            "name": "Test RSS",
            "slug": "test-rss",
            "source_type": "rss",
            "site_url": "https://example.com",
            "feed_url": "https://example.com/feed.xml",
            "language_hint": "en",
        },
    )

    monkeypatch.setattr(
        "app.services.crawl_service.fetch_feed_entries",
        lambda _: [FeedEntry(title="A1", link="https://example.com/a1")],
    )
    monkeypatch.setattr(
        "app.services.crawl_service.fetch_url_text",
        lambda *args, **kwargs: "<article><p>Hello world</p><p>FastAPI crawler</p></article>",
    )

    response = client.post("/admin/api/jobs/crawl/run")
    assert response.status_code == 200
    data = response.json()
    assert data["processed_count"] == 1
    assert data["created_count"] == 1

    articles_page = client.get("/admin/articles")
    assert articles_page.status_code == 200
    assert "A1" in articles_page.text
