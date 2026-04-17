from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.system_setting import SystemSetting

DEFAULT_SYSTEM_SETTINGS: list[dict[str, str]] = [
    {
        "setting_key": "scheduler.enabled",
        "setting_value": "true",
        "description": "是否启用 APScheduler 自动调度",
    },
    {
        "setting_key": "scheduler.timezone",
        "setting_value": "Asia/Shanghai",
        "description": "调度任务时区",
    },
    {
        "setting_key": "scheduler.crawl_cron",
        "setting_value": "0 */2 * * *",
        "description": "抓取任务 cron",
    },
    {
        "setting_key": "scheduler.process_cron",
        "setting_value": "10 */2 * * *",
        "description": "文章处理任务 cron",
    },
    {
        "setting_key": "scheduler.report_cron",
        "setting_value": "0 18 * * *",
        "description": "日报生成任务 cron",
    },
    {
        "setting_key": "scheduler.push_cron",
        "setting_value": "5 18 * * *",
        "description": "飞书推送任务 cron",
    },
    {
        "setting_key": "report.max_articles_per_day",
        "setting_value": "30",
        "description": "日报每天最多展示文章数",
    },
]


def ensure_default_settings(session: Session) -> None:
    existing_keys = set(session.scalars(select(SystemSetting.setting_key)))
    created = False
    for item in DEFAULT_SYSTEM_SETTINGS:
        if item["setting_key"] in existing_keys:
            continue
        session.add(SystemSetting(**item))
        created = True
    if created:
        session.commit()


def list_system_settings(session: Session) -> list[SystemSetting]:
    ensure_default_settings(session)
    return list(session.scalars(select(SystemSetting).order_by(SystemSetting.setting_key.asc())))


def get_setting_map(session: Session) -> dict[str, str]:
    ensure_default_settings(session)
    settings = list_system_settings(session)
    return {item.setting_key: item.setting_value for item in settings}


def get_setting_value(session: Session, setting_key: str, default: Optional[str] = None) -> Optional[str]:
    statement = select(SystemSetting).where(SystemSetting.setting_key == setting_key).limit(1)
    record = session.scalar(statement)
    return record.setting_value if record else default


def upsert_setting(session: Session, setting_key: str, setting_value: str, description: str = "") -> SystemSetting:
    statement = select(SystemSetting).where(SystemSetting.setting_key == setting_key).limit(1)
    record = session.scalar(statement)
    if record is None:
        record = SystemSetting(setting_key=setting_key, setting_value=setting_value, description=description)
    else:
        record.setting_value = setting_value
        if description:
            record.description = description
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def upsert_many(session: Session, items: Iterable[dict[str, str]]) -> list[SystemSetting]:
    result: list[SystemSetting] = []
    for item in items:
        result.append(
            upsert_setting(
                session,
                setting_key=item["setting_key"],
                setting_value=item.get("setting_value", ""),
                description=item.get("description", ""),
            )
        )
    return result
