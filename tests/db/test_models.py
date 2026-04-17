from __future__ import annotations

from app.db.models.model_config import ModelConfig
from app.db.models.source import Source


def test_source_model_has_expected_fields():
    assert hasattr(Source, "name")
    assert hasattr(Source, "source_type")
    assert hasattr(Source, "enabled")


def test_model_config_has_expected_fields():
    assert hasattr(ModelConfig, "task_type")
    assert hasattr(ModelConfig, "base_url")
    assert hasattr(ModelConfig, "api_key_env_name")

