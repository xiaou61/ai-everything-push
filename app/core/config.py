from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "技术论坛日报")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    app_debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./tech_daily.db")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    feishu_webhook_url: str = os.getenv("FEISHU_WEBHOOK_URL", "")
    site_base_url: str = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    normalized_database_url = _normalize_database_url(settings.database_url)
    return Settings(
        app_name=settings.app_name,
        app_env=settings.app_env,
        app_host=settings.app_host,
        app_port=settings.app_port,
        app_debug=settings.app_debug,
        database_url=normalized_database_url,
        openai_api_key=settings.openai_api_key,
        openai_base_url=settings.openai_base_url,
        feishu_webhook_url=settings.feishu_webhook_url,
        site_base_url=settings.site_base_url,
    )


def _normalize_database_url(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if not value:
        return "sqlite+pysqlite:///./tech_daily.db"

    if value.startswith("file:"):
        path = value[len("file:") :].lstrip("/")
        if not path:
            return "sqlite+pysqlite:///./tech_daily.db"
        return "sqlite+pysqlite:///" + path.replace("\\", "/")

    if "://" not in value:
        return "sqlite+pysqlite:///./tech_daily.db"

    return value
