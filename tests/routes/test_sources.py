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

