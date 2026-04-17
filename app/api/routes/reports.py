from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.templating import templates
from app.services.report_service import (
    ReportEditorItemUpdate,
    build_report_sections,
    build_report_view_data,
    get_report,
    get_report_by_date,
    list_reports,
    publish_report,
    update_report,
)

router = APIRouter(tags=["reports"])


class ReportEditorItemPayload(BaseModel):
    id: int
    display_order: Optional[int] = None
    section_name: Optional[str] = None


class ReportUpdatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    intro: Optional[str] = Field(default=None, max_length=2000)
    items: List[ReportEditorItemPayload]


@router.get("/admin/reports", response_class=HTMLResponse)
def admin_reports(request: Request, session: Session = Depends(get_db_session)):
    reports = list_reports(session)
    return templates.TemplateResponse(
        request=request,
        name="reports/list.html",
        context={"reports": reports, "title": "日报管理"},
    )


@router.get("/admin/api/reports/{report_id}")
def get_report_detail(report_id: int, session: Session = Depends(get_db_session)) -> dict:
    report = get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日报不存在")
    return _serialize_report_detail(report)


@router.put("/admin/api/reports/{report_id}")
def put_report_detail(report_id: int, payload: ReportUpdatePayload, session: Session = Depends(get_db_session)) -> dict:
    try:
        report = update_report(
            session,
            report_id,
            payload.title,
            payload.intro,
            [ReportEditorItemUpdate(id=item.id, display_order=item.display_order, section_name=item.section_name) for item in payload.items],
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if detail == "日报不存在" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc

    return _serialize_report_detail(report)


@router.post("/admin/api/reports/{report_id}/publish")
def post_publish_report(report_id: int, session: Session = Depends(get_db_session)) -> dict:
    try:
        report = publish_report(session, report_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {
        "message": f"{report.report_date.isoformat()} 的日报已重新发布。",
        "html_url": report.html_url,
        "report": _serialize_report_detail(report),
    }


@router.get("/daily/{report_date}", response_class=HTMLResponse)
def read_report(report_date: date, request: Request, session: Session = Depends(get_db_session)):
    report = get_report_by_date(session, report_date)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日报不存在")

    return templates.TemplateResponse(
        request=request,
        name="reports/public.html",
        context={
            "report": report,
            "sections": build_report_sections(report),
            "report_view": build_report_view_data(report),
        },
    )


def _serialize_report_detail(report) -> dict:
    return {
        "id": report.id,
        "report_date": report.report_date.isoformat(),
        "title": report.title,
        "intro": report.intro,
        "status": report.status,
        "html_path": report.html_path,
        "html_url": report.html_url,
        "source_count": report.source_count,
        "article_count": report.article_count,
        "feishu_pushed": report.feishu_pushed,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
        "items": [
            {
                "id": item.id,
                "article_id": item.article_id,
                "display_order": item.display_order,
                "section_name": item.section_name or "技术观察",
                "article_title": item.article.title,
                "generated_title": item.article.content.generated_title if item.article.content else None,
                "summary": item.article.content.summary if item.article.content else None,
                "category": item.article.content.category if item.article.content else None,
                "canonical_url": item.article.canonical_url,
                "source_name": item.article.source.name if item.article.source else "未知来源",
            }
            for item in sorted(report.items, key=lambda current: current.display_order)
        ],
    }
