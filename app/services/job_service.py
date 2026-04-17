from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.job_run import JobRun


def list_job_runs(session: Session, limit: int = 100) -> list[JobRun]:
    statement = select(JobRun).order_by(JobRun.started_at.desc(), JobRun.id.desc()).limit(limit)
    return list(session.scalars(statement))


def list_recent_job_runs(session: Session, limit: int = 8) -> list[JobRun]:
    return list_job_runs(session, limit=limit)

