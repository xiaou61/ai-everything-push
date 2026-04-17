from __future__ import annotations

from datetime import datetime
import json
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
        return _finish_job(session, job, status="skipped", message="未配置 FEISHU_WEBHOOK_URL")

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
    try:
        response_data = send_feishu_payload(settings.feishu_webhook_url, payload)
    except Exception as exc:  # noqa: BLE001
        return _finish_job(session, job, status="failed", message="飞书推送失败", detail=str(exc))

    report.feishu_pushed = True
    session.add(report)
    details = {
        "report_id": report.id,
        "report_date": report.report_date.isoformat(),
        "response": response_data,
    }
    return _finish_job(
        session,
        job,
        status="success",
        message="推送成功",
        processed_count=1,
        details=details,
        extra_result={"report_id": report.id},
    )


def send_feishu_test_message(title: str, message: str) -> dict:
    settings = get_settings()
    if not settings.feishu_webhook_url:
        return {"status": "skipped", "message": "未配置 FEISHU_WEBHOOK_URL", "detail": ""}

    payload = build_text_payload(title=title, message=message)
    try:
        send_feishu_payload(settings.feishu_webhook_url, payload)
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "message": "飞书测试消息发送失败", "detail": str(exc)}

    return {"status": "success", "message": "飞书测试消息发送成功", "detail": ""}


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


def build_text_payload(title: str, message: str) -> dict:
    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [
                        [{"tag": "text", "text": message}],
                        [{"tag": "text", "text": f"发送时间：{datetime.utcnow().isoformat()}Z"}],
                    ],
                }
            }
        },
    }


def send_feishu_payload(webhook_url: str, payload: dict) -> dict:
    with httpx.Client(timeout=20.0) as client:
        response = client.post(webhook_url, json=payload)
        response.raise_for_status()

    try:
        data = response.json()
    except ValueError:
        return {"status_code": response.status_code, "text": response.text[:500]}

    if isinstance(data, dict) and data.get("code") not in (None, 0):
        msg = str(data.get("msg") or data.get("message") or "飞书返回异常")
        raise ValueError(msg)

    return data if isinstance(data, dict) else {"response": data}


def _finish_job(
    session: Session,
    job: JobRun,
    status: str,
    message: str,
    detail: str = "",
    processed_count: int = 0,
    details: Optional[dict] = None,
    extra_result: Optional[dict] = None,
) -> dict:
    job.status = status
    job.finished_at = datetime.utcnow()
    job.processed_count = processed_count
    job.error_message = None if status == "success" else (detail or message)
    job.details_json = json.dumps(details, ensure_ascii=False) if details else None
    session.add(job)
    session.commit()

    result = {
        "status": status,
        "message": message,
    }
    if detail:
        result["detail"] = detail
    if extra_result:
        result.update(extra_result)
    return result
