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
from app.services.system_setting_service import get_setting_value


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

    template_context = build_report_template_context(
        report=report,
        highlights=highlights or ["今日暂无重点摘要"],
        site_base_url=settings.site_base_url,
    )
    title_template = get_setting_value(session, "feishu.report_title_template", "{{report_title}}") or "{{report_title}}"
    body_template = get_setting_value(
        session,
        "feishu.report_body_template",
        (
            "日期：{{report_date}}\n"
            "导语：{{report_intro}}\n"
            "共整理 {{article_count}} 篇文章，覆盖 {{source_count}} 个来源。\n"
            "今日看点：\n"
            "{{highlights_bullets}}\n"
            "完整阅读：{{report_url}}"
        ),
    ) or ""
    rendered_title = render_feishu_template(title_template, template_context).strip() or report.title
    rendered_body = render_feishu_template(body_template, template_context).strip() or template_context["highlights_bullets"]

    payload = build_report_payload(title=rendered_title, body=rendered_body)
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


def build_report_template_context(report: DailyReport, highlights: list[str], site_base_url: str) -> dict[str, str]:
    report_url = report.html_url or f"{site_base_url}/daily/{report.report_date.isoformat()}"
    safe_highlights = highlights or ["今日暂无重点摘要"]
    return {
        "report_title": report.title or "",
        "report_date": report.report_date.isoformat(),
        "report_intro": report.intro or "",
        "article_count": str(report.article_count or 0),
        "source_count": str(report.source_count or 0),
        "report_url": report_url,
        "highlights_bullets": "\n".join(f"• {item}" for item in safe_highlights),
    }


def render_feishu_template(template: str, context: dict[str, str]) -> str:
    rendered = template or ""
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered


def build_report_payload(title: str, body: str) -> dict:
    lines = [line.strip() for line in (body or "").splitlines() if line.strip()]
    content_block = [[{"tag": "text", "text": line}] for line in lines]
    if not content_block:
        content_block = [[{"tag": "text", "text": "今日暂无推送内容。"}]]

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
