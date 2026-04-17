from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.database_admin_service import (
    cleanup_failed_articles,
    cleanup_old_job_runs,
    delete_report_record,
    get_database_overview,
)

router = APIRouter(prefix="/admin/api/database", tags=["database-admin"])


class JobCleanupRequest(BaseModel):
    keep_days: int = Field(default=14, ge=0, le=3650)


@router.get("/overview")
def get_database_overview_data(session: Session = Depends(get_db_session)) -> dict:
    return get_database_overview(session)


@router.post("/maintenance/jobs/cleanup")
def post_cleanup_old_jobs(payload: JobCleanupRequest, session: Session = Depends(get_db_session)) -> dict:
    try:
        result = cleanup_old_job_runs(session, payload.keep_days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_dict()


@router.post("/maintenance/articles/failed/cleanup")
def post_cleanup_failed_articles(session: Session = Depends(get_db_session)) -> dict:
    result = cleanup_failed_articles(session)
    return result.to_dict()


@router.delete("/reports/{report_id}")
def delete_report(report_id: int, session: Session = Depends(get_db_session)) -> dict:
    try:
        result = delete_report_record(session, report_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.to_dict()
