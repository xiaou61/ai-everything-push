from __future__ import annotations

from app.services.job_service import JobAlreadyRunningError
from app.services.scheduler.runtime import SchedulerRuntime, build_schedule_config


def test_build_schedule_config():
    config = build_schedule_config(
        {
            "scheduler.crawl_cron": "0 9 * * *",
            "scheduler.process_cron": "5 9 * * *",
            "scheduler.report_cron": "0 18 * * *",
            "scheduler.push_cron": "5 18 * * *",
        }
    )
    assert len(config) == 4
    assert config[0]["job_id"] == "crawl_sources_job"
    assert config[2]["cron"] == "0 18 * * *"


def test_scheduler_runtime_ignores_job_conflict(monkeypatch):
    runtime = SchedulerRuntime()
    monkeypatch.setattr(
        "app.services.scheduler.runtime.crawl_enabled_sources",
        lambda session, trigger_type="manual": (_ for _ in ()).throw(JobAlreadyRunningError("busy")),
    )

    runtime._run_crawl_job()
