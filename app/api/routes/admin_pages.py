from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.templating import templates
from app.services.article_service import list_articles
from app.services.dashboard_service import load_dashboard_stats
from app.services.job_service import list_job_runs, list_recent_job_runs
from app.services.model_config_service import list_model_configs
from app.services.source_service import get_source, list_sources
from app.services.scheduler.runtime import scheduler_runtime

router = APIRouter(tags=["admin-pages"])


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, session: Session = Depends(get_db_session)):
    stats = load_dashboard_stats(session)
    recent_jobs = list_recent_job_runs(session)
    scheduler_status = scheduler_runtime.get_status()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "stats": stats,
            "recent_jobs": recent_jobs,
            "scheduler_status": scheduler_status,
            "title": "仪表盘",
        },
    )


@router.get("/admin/sources", response_class=HTMLResponse)
def admin_sources(request: Request, session: Session = Depends(get_db_session)):
    sources = list_sources(session)
    return templates.TemplateResponse(
        request=request,
        name="sources/list.html",
        context={"sources": sources, "title": "内容源管理"},
    )


@router.get("/admin/sources/new", response_class=HTMLResponse)
def admin_source_new(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sources/form.html",
        context={"source": None, "title": "新增内容源"},
    )


@router.get("/admin/sources/{source_id}/edit", response_class=HTMLResponse)
def admin_source_edit(source_id: int, request: Request, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")
    return templates.TemplateResponse(
        request=request,
        name="sources/form.html",
        context={"source": source, "title": "编辑内容源"},
    )


@router.get("/admin/models", response_class=HTMLResponse)
def admin_models(request: Request, session: Session = Depends(get_db_session)):
    configs = list_model_configs(session)
    return templates.TemplateResponse(
        request=request,
        name="models/list.html",
        context={"configs": configs, "title": "模型配置"},
    )


@router.get("/admin/articles", response_class=HTMLResponse)
def admin_articles(request: Request, session: Session = Depends(get_db_session)):
    articles = list_articles(session)
    return templates.TemplateResponse(
        request=request,
        name="articles/list.html",
        context={"articles": articles, "title": "文章列表"},
    )


@router.get("/admin/jobs", response_class=HTMLResponse)
def admin_jobs(request: Request, session: Session = Depends(get_db_session)):
    jobs = list_job_runs(session)
    return templates.TemplateResponse(
        request=request,
        name="jobs/list.html",
        context={"jobs": jobs, "title": "任务日志"},
    )
