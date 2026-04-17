from __future__ import annotations


def test_get_feishu_status_route(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.settings.get_feishu_status",
        lambda: {
            "configured": True,
            "masked_webhook": "https://open.feishu.cn/****",
            "site_base_url": "http://127.0.0.1:8000",
            "message": "已配置 FEISHU_WEBHOOK_URL，可发送测试消息。",
        },
    )

    response = client.get("/admin/api/integrations/feishu/status")
    assert response.status_code == 200
    assert response.json()["configured"] is True


def test_post_feishu_test_message_route(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.settings.send_feishu_test_message",
        lambda title, message: {
            "status": "success",
            "message": f"{title}:{message}",
            "detail": "",
        },
    )

    response = client.post(
        "/admin/api/integrations/feishu/test",
        json={
            "title": "联调标题",
            "message": "联调消息",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
