from __future__ import annotations

from datetime import datetime

from app.core.database import SessionLocal
from app.services.digest import DigestService
from app.services.feishu import FeishuService
from app.services.ingestion import IngestionService


def run_source_sync_job() -> None:
    with SessionLocal() as db:
        IngestionService(db).sync_all_sources()


def run_daily_digest_job() -> None:
    with SessionLocal() as db:
        digest = DigestService().generate_digest(db, datetime.now().date())
        if digest.article_count == 0:
            return
        feishu_service = FeishuService()
        if feishu_service.settings.feishu_webhook_url:
            feishu_service.push_digest(digest)
            db.commit()

