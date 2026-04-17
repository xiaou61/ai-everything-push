from __future__ import annotations

from app.services.scheduler.runtime import build_schedule_config


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
