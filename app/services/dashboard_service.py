from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.article import Article
from app.db.models.job_run import JobRun
from app.db.models.model_config import ModelConfig
from app.db.models.report import DailyReport
from app.db.models.source import Source


def load_dashboard_stats(session: Session) -> dict:
    return {
        "source_count": session.scalar(select(func.count()).select_from(Source)) or 0,
        "enabled_source_count": session.scalar(
            select(func.count()).select_from(Source).where(Source.enabled.is_(True))
        )
        or 0,
        "article_count": session.scalar(select(func.count()).select_from(Article)) or 0,
        "report_count": session.scalar(select(func.count()).select_from(DailyReport)) or 0,
        "model_count": session.scalar(select(func.count()).select_from(ModelConfig)) or 0,
        "job_count": session.scalar(select(func.count()).select_from(JobRun)) or 0,
    }
