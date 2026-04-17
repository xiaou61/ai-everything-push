from __future__ import annotations


def test_admin_settings_page(client):
    response = client.get("/admin/settings")
    assert response.status_code == 200
    assert "系统设置" in response.text
    assert "scheduler.crawl_cron" not in response.text


def test_upsert_setting_via_api(client):
    response = client.post(
        "/admin/api/settings",
        json={
            "setting_key": "report.max_articles_per_day",
            "setting_value": "12",
            "description": "日报每天最多展示文章数",
        },
    )
    assert response.status_code == 201
    assert response.json()["setting_value"] == "12"

    settings_response = client.get("/admin/api/settings")
    assert settings_response.status_code == 200
    value_map = {item["setting_key"]: item["setting_value"] for item in settings_response.json()}
    assert value_map["report.max_articles_per_day"] == "12"


def test_default_settings_include_feishu_templates(client):
    response = client.get("/admin/api/settings")
    assert response.status_code == 200
    value_map = {item["setting_key"]: item["setting_value"] for item in response.json()}
    assert "feishu.report_title_template" in value_map
    assert "feishu.report_body_template" in value_map


def test_save_settings_form(client):
    response = client.post(
        "/admin/settings/save",
        data={
            "scheduler_enabled": "false",
            "scheduler_timezone": "Asia/Shanghai",
            "scheduler_crawl_cron": "0 9 * * *",
            "scheduler_process_cron": "5 9 * * *",
            "scheduler_report_cron": "0 18 * * *",
            "scheduler_push_cron": "5 18 * * *",
            "report_max_articles_per_day": "20",
            "feishu_report_title_template": "日报：{{report_date}}",
            "feishu_report_body_template": "链接：{{report_url}}",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    settings_response = client.get("/admin/api/settings")
    value_map = {item["setting_key"]: item["setting_value"] for item in settings_response.json()}
    assert value_map["scheduler.enabled"] == "false"
    assert value_map["report.max_articles_per_day"] == "20"
    assert value_map["feishu.report_title_template"] == "日报：{{report_date}}"
    assert value_map["feishu.report_body_template"] == "链接：{{report_url}}"
