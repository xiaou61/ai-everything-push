from __future__ import annotations


def test_get_source_rule_template_for_web_source(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "Anthropic Engineering",
            "slug": "anthropic-engineering",
            "source_type": "web",
            "site_url": "https://www.anthropic.com/engineering",
            "list_url": "https://www.anthropic.com/engineering",
            "language_hint": "en",
        },
    )
    source_id = source_response.json()["id"]

    response = client.get(f"/admin/api/sources/{source_id}/rules/template")
    assert response.status_code == 200

    payload = response.json()
    assert payload["available"] is True
    assert payload["requires_rule"] is True
    assert payload["payload"]["list_item_selector"] == "article"
    assert payload["payload"]["content_selector"] == "article"


def test_get_source_rule_template_for_rss_source(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "美团技术团队",
            "slug": "meituan-tech",
            "source_type": "rss",
            "site_url": "https://tech.meituan.com/",
            "feed_url": "https://tech.meituan.com/feed/",
            "language_hint": "zh",
        },
    )
    source_id = source_response.json()["id"]

    response = client.get(f"/admin/api/sources/{source_id}/rules/template")
    assert response.status_code == 200

    payload = response.json()
    assert payload["available"] is False
    assert payload["requires_rule"] is False
    assert payload["payload"] is None
