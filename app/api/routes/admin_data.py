from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.article_service import list_articles
from app.services.dashboard_service import load_dashboard_source_health, load_dashboard_stats
from app.services.job_service import list_job_runs, list_recent_job_runs
from app.services.report_service import list_reports
from app.services.scheduler.runtime import scheduler_runtime
from app.services.starter_preset_service import apply_starter_presets, get_starter_overview

router = APIRouter(prefix="/admin/api", tags=["admin-data"])


@router.get("/dashboard")
def get_dashboard_data(session: Session = Depends(get_db_session)) -> dict:
    stats = load_dashboard_stats(session)
    source_health = load_dashboard_source_health(session)
    recent_jobs = [_serialize_job(item) for item in list_recent_job_runs(session)]
    scheduler_status = scheduler_runtime.get_status()
    return {
        "stats": stats,
        "source_health_summary": source_health["source_health_summary"],
        "source_alerts": source_health["source_alerts"],
        "recent_jobs": recent_jobs,
        "scheduler_status": {
            "available": scheduler_status.available,
            "running": scheduler_status.running,
            "enabled": scheduler_status.enabled,
            "jobs": scheduler_status.jobs,
            "message": scheduler_status.message,
        },
        "starter": get_starter_overview(session),
    }


@router.get("/articles")
def get_articles(limit: int = 100, session: Session = Depends(get_db_session)) -> list[dict]:
    articles = list_articles(session, limit=limit)
    return [
        {
            "id": item.id,
            "title": item.title,
            "canonical_url": item.canonical_url,
            "language": item.language,
            "status": item.status,
            "source_name": item.source.name if item.source else "",
            "source_id": item.source_id,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "generated_title": item.content.generated_title if item.content else None,
            "summary": item.content.summary if item.content else None,
            "category": item.content.category if item.content else None,
            "has_content": bool(item.content and item.content.clean_content),
        }
        for item in articles
    ]


@router.get("/reports")
def get_reports(session: Session = Depends(get_db_session)) -> list[dict]:
    reports = list_reports(session)
    return [
        {
            "id": item.id,
            "report_date": item.report_date.isoformat(),
            "title": item.title,
            "intro": item.intro,
            "status": item.status,
            "html_path": item.html_path,
            "html_url": item.html_url,
            "source_count": item.source_count,
            "article_count": item.article_count,
            "feishu_pushed": item.feishu_pushed,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in reports
    ]


@router.get("/jobs")
def get_jobs(limit: int = 100, session: Session = Depends(get_db_session)) -> list[dict]:
    return [_serialize_job(item) for item in list_job_runs(session, limit=limit)]


@router.get("/scheduler/status")
def get_scheduler_status() -> dict:
    scheduler_status = scheduler_runtime.get_status()
    return {
        "available": scheduler_status.available,
        "running": scheduler_status.running,
        "enabled": scheduler_status.enabled,
        "jobs": scheduler_status.jobs,
        "message": scheduler_status.message,
    }


@router.get("/bootstrap/starter")
def get_starter_data(session: Session = Depends(get_db_session)) -> dict:
    return get_starter_overview(session)


@router.post("/bootstrap/starter")
def post_starter_data(session: Session = Depends(get_db_session)) -> dict:
    return apply_starter_presets(session)


def _serialize_job(item) -> dict:
    return {
        "id": item.id,
        "job_name": item.job_name,
        "trigger_type": item.trigger_type,
        "status": item.status,
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "finished_at": item.finished_at.isoformat() if item.finished_at else None,
        "processed_count": item.processed_count,
        "error_message": item.error_message,
        "details_json": item.details_json,
    }
