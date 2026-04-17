from __future__ import annotations


def test_create_source_from_form(client):
    response = client.post(
        "/admin/sources/save",
        data={
            "name": "表单内容源",
            "slug": "form-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
            "language_hint": "zh",
            "category": "测试分类",
            "crawl_interval_minutes": "60",
            "enabled": "on",
            "include_in_daily": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    list_response = client.get("/admin/api/sources")
    data = list_response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "form-source"


def test_update_source_from_form(client):
    created = client.post(
        "/admin/api/sources",
        json={
            "name": "源A",
            "slug": "source-a",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/a",
        },
    )
    source_id = created.json()["id"]

    response = client.post(
        f"/admin/sources/{source_id}/save",
        data={
            "name": "源A更新",
            "slug": "source-a",
            "source_type": "rss",
            "site_url": "https://example.com",
            "feed_url": "https://example.com/feed.xml",
            "crawl_interval_minutes": "30",
            "enabled": "on",
            "include_in_daily": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    updated = client.get("/admin/api/sources").json()[0]
    assert updated["name"] == "源A更新"
    assert updated["source_type"] == "rss"


def test_run_job_from_form(client, monkeypatch):
    called = {"crawl": 0}

    def fake_crawl(session):
        called["crawl"] += 1
        return None

    monkeypatch.setattr("app.api.routes.admin_actions.crawl_enabled_sources", fake_crawl)
    response = client.post(
        "/admin/jobs/run/crawl",
        data={"next": "/admin/jobs"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/jobs"
    assert called["crawl"] == 1
