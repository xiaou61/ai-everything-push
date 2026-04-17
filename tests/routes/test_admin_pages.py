from __future__ import annotations


def test_source_new_page(client):
    response = client.get("/admin/sources/new")
    assert response.status_code == 200
    assert "新增内容源" in response.text


def test_jobs_page(client):
    response = client.get("/admin/jobs")
    assert response.status_code == 200
    assert "任务日志" in response.text

