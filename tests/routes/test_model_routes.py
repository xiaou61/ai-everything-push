from __future__ import annotations


def test_create_task_model_config(client):
    response = client.post(
        "/admin/api/models",
        json={
            "task_type": "translation",
            "provider_name": "relay",
            "model_name": "gpt-4.1-mini",
            "base_url": "https://relay.example.com/v1",
            "api_key_env_name": "OPENAI_API_KEY",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task_type"] == "translation"
    assert data["provider_name"] == "relay"


def test_default_model_is_replaced_when_new_default_created(client):
    first = client.post(
        "/admin/api/models",
        json={
            "task_type": "summary",
            "provider_name": "relay",
            "model_name": "model-a",
            "base_url": "https://relay.example.com/v1",
            "api_key_env_name": "OPENAI_API_KEY",
            "is_default": True,
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/admin/api/models",
        json={
            "task_type": "summary",
            "provider_name": "relay",
            "model_name": "model-b",
            "base_url": "https://relay.example.com/v1",
            "api_key_env_name": "OPENAI_API_KEY",
            "is_default": True,
        },
    )
    assert second.status_code == 201

    records = client.get("/admin/api/models").json()
    default_records = [item for item in records if item["task_type"] == "summary" and item["is_default"]]
    assert len(default_records) == 1
    assert default_records[0]["model_name"] == "model-b"
