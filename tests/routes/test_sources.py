from __future__ import annotations


def test_create_source(client):
    response = client.post(
        "/admin/api/sources",
        json={
            "name": "美团技术团队",
            "slug": "meituan-tech",
            "source_type": "web",
            "site_url": "https://tech.meituan.com",
            "list_url": "https://tech.meituan.com",
            "category": "国内技术博客",
            "language_hint": "zh",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "美团技术团队"
    assert data["source_type"] == "web"
    assert data["consecutive_failures"] == 0
    assert data["last_crawl_status"] is None
    assert data["last_crawl_error"] is None
    assert data["health_level"] == "idle"
    assert data["health_label"] == "未抓取"
    assert data["last_success_at"] is None
    assert data["last_failure_at"] is None
    assert data["last_retry_attempts"] == 0
    assert data["next_retry_at"] is None
    assert data["can_retry_now"] is False


def test_toggle_source(client):
    created = client.post(
        "/admin/api/sources",
        json={
            "name": "Anthropic Engineering",
            "slug": "anthropic-engineering",
            "source_type": "web",
            "site_url": "https://www.anthropic.com",
            "list_url": "https://www.anthropic.com/engineering",
            "category": "海外技术博客",
            "language_hint": "en",
        },
    )
    source_id = created.json()["id"]

    response = client.post(f"/admin/api/sources/{source_id}/toggle")
    assert response.status_code == 200
    assert response.json()["enabled"] is False
