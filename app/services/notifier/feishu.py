from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.job_run import JobRun
from app.db.models.report import DailyReport
from app.services.report_service import build_report_sections, get_report_by_date


def push_report_to_feishu(session: Session, report_date) -> dict:
    settings = get_settings()
    report = get_report_by_date(session, report_date)
    if report is None:
        raise ValueError("日报不存在")

    job = JobRun(
        job_name="push_report_job",
        trigger_type="manual",
        status="running",
        started_at=datetime.utcnow(),
        processed_count=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    if not settings.feishu_webhook_url:
        job.status = "skipped"
        job.finished_at = datetime.utcnow()
        job.error_message = "未配置 FEISHU_WEBHOOK_URL"
        session.add(job)
        session.commit()
        return {"status": "skipped", "message": "未配置 FEISHU_WEBHOOK_URL"}

    sections = build_report_sections(report)
    highlights = []
    for items in sections.values():
        for item in items:
            title = item.article.content.generated_title if item.article.content and item.article.content.generated_title else item.article.title
            highlights.append(title)
            if len(highlights) >= 3:
                break
        if len(highlights) >= 3:
            break

    payload = build_report_payload(
        title=report.title,
        highlights=highlights or ["今日暂无重点摘要"],
        url=report.html_url or f"{settings.site_base_url}/daily/{report.report_date.isoformat()}",
        article_count=report.article_count,
    )
    with httpx.Client(timeout=20.0) as client:
        response = client.post(settings.feishu_webhook_url, json=payload)
        response.raise_for_status()

    report.feishu_pushed = True
    session.add(report)
    job.status = "success"
    job.finished_at = datetime.utcnow()
    job.processed_count = 1
    session.add(job)
    session.commit()
    return {"status": "success", "report_id": report.id}


def build_report_payload(title: str, highlights: list[str], url: str, article_count: int) -> dict:
    content_block = [[{"tag": "text", "text": f"共整理 {article_count} 篇文章"}]]
    for line in highlights:
        content_block.append([{"tag": "text", "text": f"• {line}"}])
    content_block.append([{"tag": "a", "text": "查看完整日报", "href": url}])

    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content_block,
                }
            }
        },
    }

