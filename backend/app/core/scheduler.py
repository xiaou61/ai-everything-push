from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings


scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def configure_scheduler() -> BackgroundScheduler:
    from app.services.jobs import run_daily_digest_job, run_source_sync_job

    if scheduler.get_job("sync-sources") is None:
        settings = get_settings()
        scheduler.add_job(
            run_source_sync_job,
            trigger="interval",
            minutes=settings.source_sync_interval_minutes,
            id="sync-sources",
            replace_existing=True,
        )
        scheduler.add_job(
            run_daily_digest_job,
            trigger=CronTrigger.from_crontab(settings.daily_digest_cron, timezone="Asia/Shanghai"),
            id="daily-digest",
            replace_existing=True,
        )
    return scheduler

