from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.article_processing_service import process_pending_articles
from app.services.crawl_service import crawl_enabled_sources
from app.services.job_service import JobAlreadyRunningError
from app.services.notifier.feishu import push_report_to_feishu
from app.services.report_service import generate_daily_report

router = APIRouter(prefix="/admin/api/jobs", tags=["jobs"])


@router.post("/crawl/run")
def run_crawl_job(session: Session = Depends(get_db_session)) -> dict:
    try:
        summary = crawl_enabled_sources(session)
    except JobAlreadyRunningError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {
        "job_id": summary.job_id,
        "job_name": "crawl_sources_job",
        "source_count": summary.source_count,
        "processed_count": summary.processed_count,
        "created_count": summary.created_count,
        "updated_count": summary.updated_count,
        "skipped_count": summary.skipped_count,
        "errors": summary.errors,
    }


@router.post("/process/run")
def run_process_job(session: Session = Depends(get_db_session)) -> dict:
    try:
        summary = process_pending_articles(session)
    except JobAlreadyRunningError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {
        "job_id": summary.job_id,
        "job_name": "process_articles_job",
        "processed_count": summary.processed_count,
        "success_count": summary.success_count,
        "failed_count": summary.failed_count,
        "errors": summary.errors,
    }


@router.post("/report/run")
def run_report_job(report_date: Optional[date] = None, session: Session = Depends(get_db_session)) -> dict:
    try:
        summary = generate_daily_report(session, report_date)
    except JobAlreadyRunningError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {
        "job_id": summary.job_id,
        "report_id": summary.report_id,
        "report_date": summary.report_date.isoformat(),
        "article_count": summary.article_count,
        "html_url": summary.html_url,
    }


@router.post("/push/run")
def run_push_job(report_date: Optional[date] = None, session: Session = Depends(get_db_session)) -> dict:
    target_date = report_date or date.today()
    try:
        result = push_report_to_feishu(session, target_date)
    except JobAlreadyRunningError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return result
