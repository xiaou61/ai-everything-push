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

    sources_response = client.get("/admin/api/sources")
    source = sources_response.json()[0]
    assert source["last_crawl_status"] == "success"
    assert source["consecutive_failures"] == 0
    assert source["last_crawl_processed_count"] == 1
    assert source["last_crawl_error"] is None

    articles_page = client.get("/admin/articles")
    assert articles_page.status_code == 200
    assert "A1" in articles_page.text


def test_run_crawl_job_updates_source_failure_state(client, monkeypatch):
    client.post(
        "/admin/api/sources",
        json={
            "name": "Broken RSS",
            "slug": "broken-rss",
            "source_type": "rss",
            "site_url": "https://broken.example.com",
            "feed_url": "https://broken.example.com/feed.xml",
            "language_hint": "en",
        },
    )

    def raise_fetch(_):
        raise ValueError("源站超时")

    monkeypatch.setattr("app.services.crawl_service.fetch_feed_entries", raise_fetch)

    response = client.post("/admin/api/jobs/crawl/run")
    assert response.status_code == 200

    sources_response = client.get("/admin/api/sources")
    source = sources_response.json()[0]
    assert source["last_crawl_status"] == "failed"
    assert source["consecutive_failures"] == 1
    assert source["last_crawl_processed_count"] == 0
    assert "源站超时" in source["last_crawl_error"]
