from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Article, DailyDigest, Source
from app.schemas.dashboard import DashboardResponse


router = APIRouter()


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    latest_digest = db.scalar(select(DailyDigest).order_by(DailyDigest.digest_date.desc()))
    latest_sync = db.scalar(select(func.max(Source.last_synced_at)))

    return DashboardResponse(
        source_count=db.scalar(select(func.count()).select_from(Source)) or 0,
        article_count=db.scalar(select(func.count()).select_from(Article)) or 0,
        digest_count=db.scalar(select(func.count()).select_from(DailyDigest)) or 0,
        latest_digest_date=latest_digest.digest_date.isoformat() if latest_digest else None,
        latest_digest_headline=latest_digest.headline if latest_digest else None,
        latest_sync_at=latest_sync.isoformat() if isinstance(latest_sync, datetime) else None,
    )

