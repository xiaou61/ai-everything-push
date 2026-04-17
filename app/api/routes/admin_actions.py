from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.form_utils import parse_simple_form
from app.schemas.source import SourceCreate, SourceUpdate
from app.services.article_processing_service import process_pending_articles
from app.services.crawl_service import crawl_enabled_sources
from app.services.notifier.feishu import push_report_to_feishu
from app.services.report_service import generate_daily_report
from app.services.source_service import create_source, get_source, toggle_source, update_source

router = APIRouter(tags=["admin-actions"])


@router.post("/admin/sources/save")
async def create_source_from_form(request: Request, session: Session = Depends(get_db_session)):
    form = parse_simple_form(await request.body())
    payload = SourceCreate(
        name=form.get("name", "").strip(),
        slug=form.get("slug", "").strip(),
        site_url=form.get("site_url", "").strip(),
        source_type=form.get("source_type", "web").strip(),
        feed_url=_optional_value(form.get("feed_url")),
        list_url=_optional_value(form.get("list_url")),
        language_hint=_optional_value(form.get("language_hint")),
        category=_optional_value(form.get("category")),
        enabled=_parse_checkbox(form.get("enabled")),
        include_in_daily=_parse_checkbox(form.get("include_in_daily", "on")),
        crawl_interval_minutes=int(form.get("crawl_interval_minutes", "60") or "60"),
    )
    create_source(session, payload)
    return RedirectResponse(url="/admin/sources", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/sources/{source_id}/save")
async def update_source_from_form(source_id: int, request: Request, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")

    form = parse_simple_form(await request.body())
    payload = SourceUpdate(
        name=form.get("name", "").strip(),
        slug=form.get("slug", "").strip(),
        site_url=form.get("site_url", "").strip(),
        source_type=form.get("source_type", "web").strip(),
        feed_url=_optional_value(form.get("feed_url")),
        list_url=_optional_value(form.get("list_url")),
        language_hint=_optional_value(form.get("language_hint")),
        category=_optional_value(form.get("category")),
        enabled=_parse_checkbox(form.get("enabled")),
        include_in_daily=_parse_checkbox(form.get("include_in_daily", "on")),
        crawl_interval_minutes=int(form.get("crawl_interval_minutes", "60") or "60"),
    )
    update_source(session, source, payload)
    return RedirectResponse(url="/admin/sources", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/sources/{source_id}/toggle")
def toggle_source_from_form(source_id: int, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")
    toggle_source(session, source)
    return RedirectResponse(url="/admin/sources", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/jobs/run/{job_name}")
async def run_job_from_form(job_name: str, request: Request, session: Session = Depends(get_db_session)):
    form = parse_simple_form(await request.body())
    next_url = form.get("next", "/admin")
    report_date = _parse_report_date(form.get("report_date"))

    if job_name == "crawl":
        crawl_enabled_sources(session)
    elif job_name == "process":
        process_pending_articles(session)
    elif job_name == "report":
        generate_daily_report(session, report_date)
    elif job_name == "push":
        push_report_to_feishu(session, report_date or date.today())
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    return RedirectResponse(url=next_url, status_code=status.HTTP_303_SEE_OTHER)


def _optional_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_checkbox(value: str | None) -> bool:
    return (value or "").strip().lower() in {"on", "true", "1", "yes"}


def _parse_report_date(raw_value: str | None) -> date | None:
    if not raw_value:
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None
