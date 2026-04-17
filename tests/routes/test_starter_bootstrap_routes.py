from __future__ import annotations


def test_get_starter_overview(client):
    response = client.get("/admin/api/bootstrap/starter")
    assert response.status_code == 200

    payload = response.json()
    assert payload["missing_source_count"] >= 1
    assert payload["missing_model_count"] >= 1
    assert any(item["slug"] == "meituan-tech" for item in payload["sources"])
    assert any(item["task_type"] == "summary" for item in payload["models"])


def test_apply_starter_presets(client):
    response = client.post("/admin/api/bootstrap/starter")
    assert response.status_code == 200

    payload = response.json()
    assert "meituan-tech" in payload["created_sources"]
    assert "summary" in payload["created_models"]
    assert payload["overview"]["missing_source_count"] == 0
    assert payload["overview"]["missing_model_count"] == 0

    second_response = client.post("/admin/api/bootstrap/starter")
    second_payload = second_response.json()
    assert "meituan-tech" in second_payload["skipped_sources"]
    assert "summary" in second_payload["skipped_models"]
