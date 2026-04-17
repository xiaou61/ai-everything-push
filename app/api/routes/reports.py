from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.templating import templates
from app.services.report_service import build_report_sections, get_report_by_date, list_reports

router = APIRouter(tags=["reports"])


@router.get("/admin/reports", response_class=HTMLResponse)
def admin_reports(request: Request, session: Session = Depends(get_db_session)):
    reports = list_reports(session)
    return templates.TemplateResponse(
        request=request,
        name="reports/list.html",
        context={"reports": reports, "title": "日报管理"},
    )


@router.get("/daily/{report_date}", response_class=HTMLResponse)
def read_report(report_date: date, request: Request, session: Session = Depends(get_db_session)):
    report = get_report_by_date(session, report_date)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日报不存在")

    return templates.TemplateResponse(
        request=request,
        name="reports/public.html",
        context={"report": report, "sections": build_report_sections(report)},
    )

