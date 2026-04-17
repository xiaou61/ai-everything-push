from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.form_utils import parse_simple_form
from app.core.templating import templates
from app.schemas.system_setting import SystemSettingRead, SystemSettingUpsert
from app.services.scheduler.runtime import scheduler_runtime
from app.services.system_setting_service import DEFAULT_SYSTEM_SETTINGS, get_setting_map, list_system_settings, upsert_many, upsert_setting

router = APIRouter(tags=["settings"])


@router.get("/admin/settings", response_class=HTMLResponse)
def admin_settings(request: Request, session: Session = Depends(get_db_session)):
    settings = list_system_settings(session)
    setting_map = get_setting_map(session)
    scheduler_status = scheduler_runtime.get_status()
    return templates.TemplateResponse(
        request=request,
        name="settings/list.html",
        context={
            "settings": settings,
            "setting_map": setting_map,
            "title": "系统设置",
            "defaults": DEFAULT_SYSTEM_SETTINGS,
            "scheduler_status": scheduler_status,
        },
    )


@router.post("/admin/settings/save")
async def save_settings_from_form(request: Request, session: Session = Depends(get_db_session)):
    form = parse_simple_form(await request.body())
    upsert_many(
        session,
        [
            {"setting_key": "scheduler.enabled", "setting_value": form.get("scheduler_enabled", "false"), "description": "是否启用 APScheduler 自动调度"},
            {"setting_key": "scheduler.timezone", "setting_value": form.get("scheduler_timezone", "Asia/Shanghai"), "description": "调度任务时区"},
            {"setting_key": "scheduler.crawl_cron", "setting_value": form.get("scheduler_crawl_cron", "0 */2 * * *"), "description": "抓取任务 cron"},
            {"setting_key": "scheduler.process_cron", "setting_value": form.get("scheduler_process_cron", "10 */2 * * *"), "description": "文章处理任务 cron"},
            {"setting_key": "scheduler.report_cron", "setting_value": form.get("scheduler_report_cron", "0 18 * * *"), "description": "日报生成任务 cron"},
            {"setting_key": "scheduler.push_cron", "setting_value": form.get("scheduler_push_cron", "5 18 * * *"), "description": "飞书推送任务 cron"},
            {"setting_key": "report.max_articles_per_day", "setting_value": form.get("report_max_articles_per_day", "30"), "description": "日报每天最多展示文章数"},
        ],
    )
    scheduler_runtime.reload()
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/api/settings", response_model=List[SystemSettingRead])
def get_settings(session: Session = Depends(get_db_session)):
    return list_system_settings(session)


@router.post("/admin/api/settings", response_model=SystemSettingRead, status_code=status.HTTP_201_CREATED)
def post_setting(payload: SystemSettingUpsert, session: Session = Depends(get_db_session)):
    record = upsert_setting(session, payload.setting_key, payload.setting_value, payload.description)
    scheduler_runtime.reload()
    return record


@router.post("/admin/api/settings/batch")
def post_settings_batch(payload: list[SystemSettingUpsert], session: Session = Depends(get_db_session)) -> list[SystemSettingRead]:
    records = upsert_many(
        session,
        [
            {
                "setting_key": item.setting_key,
                "setting_value": item.setting_value,
                "description": item.description,
            }
            for item in payload
        ],
    )
    scheduler_runtime.reload()
    return records


@router.post("/admin/api/scheduler/reload")
def reload_scheduler() -> dict:
    status_info = scheduler_runtime.reload()
    return {
        "available": status_info.available,
        "running": status_info.running,
        "enabled": status_info.enabled,
        "jobs": status_info.jobs,
        "message": status_info.message,
    }
