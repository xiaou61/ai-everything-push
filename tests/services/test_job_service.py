from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.core.database import SessionLocal
from app.db.models import JobRun
from app.services.job_service import JobAlreadyRunningError, finish_job_run, start_job_run


def test_start_job_run_blocks_when_same_job_is_running():
    session = SessionLocal()
    try:
        session.add(
            JobRun(
                job_name="crawl_sources_job",
                trigger_type="manual",
                status="running",
                started_at=datetime.utcnow(),
                processed_count=0,
            )
        )
        session.commit()

        with pytest.raises(JobAlreadyRunningError):
            start_job_run(session, "crawl_sources_job")
    finally:
        session.close()


def test_start_job_run_expires_stale_running_job():
    session = SessionLocal()
    try:
        stale_job = JobRun(
            job_name="process_articles_job",
            trigger_type="manual",
            status="running",
            started_at=datetime.utcnow() - timedelta(hours=5),
            processed_count=0,
        )
        session.add(stale_job)
        session.commit()

        execution = start_job_run(session, "process_articles_job", stale_after_minutes=60)
        finish_job_run(session, execution, status="success", processed_count=2)

        session.refresh(stale_job)
        latest_jobs = session.query(JobRun).filter(JobRun.job_name == "process_articles_job").order_by(JobRun.id.asc()).all()
        assert stale_job.status == "timeout"
        assert stale_job.finished_at is not None
        assert latest_jobs[-1].status == "success"
        assert latest_jobs[-1].processed_count == 2
    finally:
        session.close()
