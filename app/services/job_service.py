from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock, RLock
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.job_run import JobRun

DEFAULT_RUNNING_TIMEOUT_MINUTES = 180
_JOB_LOCKS: Dict[str, Lock] = {}
_JOB_LOCKS_GUARD = RLock()


class JobAlreadyRunningError(RuntimeError):
    pass


@dataclass
class JobExecution:
    job: JobRun
    lock: Lock
    released: bool = False


def list_job_runs(session: Session, limit: int = 100) -> list[JobRun]:
    statement = select(JobRun).order_by(JobRun.started_at.desc(), JobRun.id.desc()).limit(limit)
    return list(session.scalars(statement))


def list_recent_job_runs(session: Session, limit: int = 8) -> list[JobRun]:
    return list_job_runs(session, limit=limit)


def start_job_run(
    session: Session,
    job_name: str,
    trigger_type: str = "manual",
    stale_after_minutes: int = DEFAULT_RUNNING_TIMEOUT_MINUTES,
) -> JobExecution:
    lock = _get_job_lock(job_name)
    if not lock.acquire(blocking=False):
        raise JobAlreadyRunningError(f"{job_name} 正在运行中，请稍后再试")

    try:
        expire_stale_job_runs(session, job_name, stale_after_minutes=stale_after_minutes)
        running_job = get_running_job(session, job_name)
        if running_job is not None:
            raise JobAlreadyRunningError(f"{job_name} 正在运行中，请稍后再试")

        job = JobRun(
            job_name=job_name,
            trigger_type=trigger_type,
            status="running",
            started_at=datetime.utcnow(),
            processed_count=0,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return JobExecution(job=job, lock=lock)
    except Exception:
        lock.release()
        raise


def finish_job_run(
    session: Session,
    execution: JobExecution,
    status: str,
    processed_count: int = 0,
    error_message: Optional[str] = None,
    details_json: Optional[str] = None,
) -> JobRun:
    try:
        execution.job.status = status
        execution.job.finished_at = datetime.utcnow()
        execution.job.processed_count = processed_count
        execution.job.error_message = error_message
        execution.job.details_json = details_json
        session.add(execution.job)
        session.commit()
        session.refresh(execution.job)
        return execution.job
    finally:
        release_job_execution(execution)


def get_running_job(session: Session, job_name: str) -> Optional[JobRun]:
    statement = (
        select(JobRun)
        .where(
            JobRun.job_name == job_name,
            JobRun.status == "running",
            JobRun.finished_at.is_(None),
        )
        .order_by(JobRun.started_at.desc(), JobRun.id.desc())
        .limit(1)
    )
    return session.scalar(statement)


def expire_stale_job_runs(session: Session, job_name: str, stale_after_minutes: int = DEFAULT_RUNNING_TIMEOUT_MINUTES) -> int:
    cutoff = datetime.utcnow() - timedelta(minutes=stale_after_minutes)
    timed_out_jobs = list(
        session.scalars(
            select(JobRun).where(
                JobRun.job_name == job_name,
                JobRun.status == "running",
                JobRun.finished_at.is_(None),
                JobRun.started_at < cutoff,
            )
        )
    )
    if not timed_out_jobs:
        return 0

    finished_at = datetime.utcnow()
    for job in timed_out_jobs:
        job.status = "timeout"
        job.finished_at = finished_at
        job.error_message = "任务运行超时，已自动结束。"
        session.add(job)
    session.commit()
    return len(timed_out_jobs)


def release_job_execution(execution: JobExecution) -> None:
    if execution.released:
        return
    execution.lock.release()
    execution.released = True


def reset_job_locks() -> None:
    with _JOB_LOCKS_GUARD:
        _JOB_LOCKS.clear()


def _get_job_lock(job_name: str) -> Lock:
    with _JOB_LOCKS_GUARD:
        lock = _JOB_LOCKS.get(job_name)
        if lock is None:
            lock = Lock()
            _JOB_LOCKS[job_name] = lock
        return lock
