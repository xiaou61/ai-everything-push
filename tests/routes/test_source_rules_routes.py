from __future__ import annotations


def test_create_source_rule_via_api(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "规则测试源",
            "slug": "rule-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
        },
    )
    source_id = source_response.json()["id"]

    rule_response = client.post(
        f"/admin/api/sources/{source_id}/rules",
        json={
            "list_item_selector": ".post-item",
            "link_selector": "a[href]",
            "content_selector": ".post-content",
        },
    )
    assert rule_response.status_code == 201
    assert rule_response.json()["content_selector"] == ".post-content"

    page_response = client.get(f"/admin/sources/{source_id}/rules")
    assert page_response.status_code == 200
    assert "抓取规则" in page_response.text


def test_save_source_rule_from_form(client):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "规则表单源",
            "slug": "rule-form-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
        },
    )
    source_id = source_response.json()["id"]

    response = client.post(
        f"/admin/sources/{source_id}/rules/save",
        data={
            "list_item_selector": ".card",
            "link_selector": "a[href]",
            "content_selector": "article",
            "remove_selectors": ".share,.ad",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    rule_response = client.get(f"/admin/api/sources/{source_id}/rules")
    assert rule_response.status_code == 200
    assert rule_response.json()["list_item_selector"] == ".card"


def test_preview_source_rule_list_from_form(client, monkeypatch):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "预览列表源",
            "slug": "rule-preview-list-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
        },
    )
    source_id = source_response.json()["id"]

    monkeypatch.setattr(
        "app.services.source_rule_preview_service.fetch_url_text",
        lambda *args, **kwargs: """
        <html><body>
            <div class='post-item'><a href='/a1'>文章 A1</a></div>
            <div class='post-item'><a href='/a2'>文章 A2</a></div>
        </body></html>
        """,
    )

    response = client.post(
        f"/admin/sources/{source_id}/rules/preview",
        data={
            "list_item_selector": ".post-item",
            "link_selector": "a[href]",
            "preview_mode": "list",
        },
    )
    assert response.status_code == 200
    assert "文章 A1" in response.text
    assert "预览结果" in response.text


def test_preview_source_rule_article_from_form(client, monkeypatch):
    source_response = client.post(
        "/admin/api/sources",
        json={
            "name": "预览正文源",
            "slug": "rule-preview-article-source",
            "source_type": "web",
            "site_url": "https://example.com",
            "list_url": "https://example.com/blog",
        },
    )
    source_id = source_response.json()["id"]

    def fake_fetch(url, *args, **kwargs):
        if url == "https://example.com/blog":
            return "<div class='post-item'><a href='/post-1'>文章 1</a></div>"
        return "<article><p>这是正文第一段。</p><p>这是正文第二段。</p></article>"

    monkeypatch.setattr("app.services.source_rule_preview_service.fetch_url_text", fake_fetch)

    response = client.post(
        f"/admin/sources/{source_id}/rules/preview",
        data={
            "list_item_selector": ".post-item",
            "link_selector": "a[href]",
            "content_selector": "article",
            "preview_mode": "article",
        },
    )
    assert response.status_code == 200
    assert "这是正文第一段" in response.text
