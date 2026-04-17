from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Forum Digest Platform"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "forum_digest"
    mysql_password: str = "forum_digest"
    mysql_database: str = "forum_digest"

    request_timeout_seconds: int = 20
    default_fetch_limit: int = 20
    source_sync_interval_minutes: int = 60
    daily_digest_cron: str = "0 18 * * *"
    daily_digest_site_base_url: str = "http://localhost:8000"
    frontend_dist_dir: str = "../frontend/dist"

    feishu_webhook_url: str = ""

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def frontend_dist_path(self) -> Path:
        dist_path = Path(self.frontend_dist_dir)
        if dist_path.is_absolute():
            return dist_path
        return (BACKEND_DIR / dist_path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

