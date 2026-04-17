from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.article_processing_service import process_pending_articles
from app.services.crawl_service import crawl_enabled_sources
from app.services.notifier.feishu import push_report_to_feishu
from app.services.report_service import generate_daily_report
from app.services.system_setting_service import get_setting_map

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    APSCHEDULER_AVAILABLE = True
except ImportError:  # pragma: no cover
    BackgroundScheduler = None  # type: ignore[assignment]
    CronTrigger = None  # type: ignore[assignment]
    APSCHEDULER_AVAILABLE = False

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]


@dataclass
class SchedulerStatus:
    available: bool
    running: bool
    enabled: bool
    jobs: list[dict]
    message: str = ""


def build_schedule_config(setting_map: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"job_id": "crawl_sources_job", "setting_key": "scheduler.crawl_cron", "cron": setting_map.get("scheduler.crawl_cron", "")},
        {"job_id": "process_articles_job", "setting_key": "scheduler.process_cron", "cron": setting_map.get("scheduler.process_cron", "")},
        {"job_id": "generate_report_job", "setting_key": "scheduler.report_cron", "cron": setting_map.get("scheduler.report_cron", "")},
        {"job_id": "push_report_job", "setting_key": "scheduler.push_cron", "cron": setting_map.get("scheduler.push_cron", "")},
    ]


class SchedulerRuntime:
    def __init__(self) -> None:
        self._scheduler = None
        self._last_errors: list[str] = []
        self._enabled = False

    def start(self) -> SchedulerStatus:
        settings = get_settings()
        if settings.app_env == "test":
            return self.get_status(message="测试环境下不启动调度器")

        if not APSCHEDULER_AVAILABLE:
            return self.get_status(message="未安装 APScheduler，调度器未启动")

        if self._scheduler is None:
            timezone_name = self._load_timezone()
            timezone = self._build_timezone(timezone_name)
            self._scheduler = BackgroundScheduler(timezone=timezone)

        if not self._scheduler.running:
            self._register_jobs()
            self._scheduler.start()
            logger.info("Scheduler started with %s jobs", len(self._scheduler.get_jobs()))

        return self.get_status()

    def stop(self) -> None:
        if self._scheduler is not None and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def reload(self) -> SchedulerStatus:
        settings = get_settings()
        if settings.app_env == "test":
            return self.get_status(message="测试环境下不启动调度器")

        if not APSCHEDULER_AVAILABLE:
            return self.get_status(message="未安装 APScheduler，无法重载调度器")

        if self._scheduler is None:
            return self.start()

        for job in self._scheduler.get_jobs():
            self._scheduler.remove_job(job.id)

        self._register_jobs()
        return self.get_status()

    def get_status(self, message: str = "") -> SchedulerStatus:
        jobs = []
        running = bool(self._scheduler and self._scheduler.running)
        if self._scheduler is not None:
            for job in self._scheduler.get_jobs():
                jobs.append(
                    {
                        "id": job.id,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    }
                )

        status_message = message or ("\n".join(self._last_errors) if self._last_errors else "")
        return SchedulerStatus(
            available=APSCHEDULER_AVAILABLE,
            running=running,
            enabled=self._enabled,
            jobs=jobs,
            message=status_message,
        )

    def _register_jobs(self) -> None:
        if self._scheduler is None or CronTrigger is None:
            return

        self._last_errors = []
        setting_map = self._load_setting_map()
        self._enabled = _parse_bool(setting_map.get("scheduler.enabled", "true"))
        if not self._enabled:
            return

        schedule_config = build_schedule_config(setting_map)
        job_handlers: dict[str, Callable[[], None]] = {
            "crawl_sources_job": self._run_crawl_job,
            "process_articles_job": self._run_process_job,
            "generate_report_job": self._run_report_job,
            "push_report_job": self._run_push_job,
        }

        for item in schedule_config:
            cron = item["cron"].strip()
            if not cron:
                continue
            try:
                trigger = CronTrigger.from_crontab(cron)
                self._scheduler.add_job(
                    job_handlers[item["job_id"]],
                    trigger=trigger,
                    id=item["job_id"],
                    replace_existing=True,
                    max_instances=1,
                    misfire_grace_time=120,
                )
            except Exception as exc:  # noqa: BLE001
                self._last_errors.append(f"{item['setting_key']}: {exc}")
                logger.warning("Failed to register job %s: %s", item["job_id"], exc)

    def _load_setting_map(self) -> dict[str, str]:
        session = SessionLocal()
        try:
            return get_setting_map(session)
        finally:
            session.close()

    def _load_timezone(self) -> str:
        return self._load_setting_map().get("scheduler.timezone", "Asia/Shanghai")

    def _build_timezone(self, timezone_name: str):
        if ZoneInfo is None:
            return timezone_name
        try:
            return ZoneInfo(timezone_name)
        except Exception:  # noqa: BLE001
            return ZoneInfo("UTC")

    def _run_crawl_job(self) -> None:
        session = SessionLocal()
        try:
            crawl_enabled_sources(session)
        finally:
            session.close()

    def _run_process_job(self) -> None:
        session = SessionLocal()
        try:
            process_pending_articles(session)
        finally:
            session.close()

    def _run_report_job(self) -> None:
        session = SessionLocal()
        try:
            generate_daily_report(session, date.today())
        finally:
            session.close()

    def _run_push_job(self) -> None:
        session = SessionLocal()
        try:
            push_report_to_feishu(session, date.today())
        finally:
            session.close()


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


scheduler_runtime = SchedulerRuntime()
