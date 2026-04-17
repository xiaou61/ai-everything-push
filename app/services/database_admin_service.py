from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, or_, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    Article,
    ArticleContent,
    DailyReport,
    DailyReportItem,
    JobRun,
    ModelConfig,
    Source,
    SourceRule,
    SystemSetting,
)


@dataclass
class MaintenanceResult:
    action: str
    deleted_count: int
    message: str
    extra: dict | None = None

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "deleted_count": self.deleted_count,
            "message": self.message,
            **(self.extra or {}),
        }


def get_database_overview(session: Session) -> dict:
    table_stats = [
        _build_table_stat(session, Source, "sources", "内容源", "采集入口与站点配置", Source.updated_at),
        _build_table_stat(session, SourceRule, "source_rules", "抓取规则", "网页抓取选择器和请求头", SourceRule.updated_at),
        _build_table_stat(session, Article, "articles", "文章", "抓取后的文章主记录", Article.updated_at),
        _build_table_stat(session, ArticleContent, "article_contents", "文章内容", "正文、摘要、分类和翻译结果", ArticleContent.updated_at),
        _build_table_stat(session, DailyReport, "daily_reports", "日报", "日报主记录与公开页信息", DailyReport.updated_at),
        _build_table_stat(session, DailyReportItem, "daily_report_items", "日报条目", "日报与文章关联明细"),
        _build_table_stat(session, JobRun, "job_runs", "任务日志", "抓取、处理、生成、推送执行记录", JobRun.started_at),
        _build_table_stat(session, ModelConfig, "model_configs", "模型配置", "翻译、摘要、分类和标题模型", ModelConfig.updated_at),
        _build_table_stat(session, SystemSetting, "system_settings", "系统设置", "调度器与运行时参数"),
    ]

    article_status_breakdown = [
        {"key": "crawled", "label": "待处理文章", "count": _count(session, Article, Article.status == "crawled")},
        {"key": "failed", "label": "抓取失败文章", "count": _count(session, Article, Article.status == "failed")},
        {
            "key": "ai_failed",
            "label": "AI 处理失败",
            "count": session.scalar(
                select(func.count()).select_from(ArticleContent).where(ArticleContent.ai_status == "failed")
            )
            or 0,
        },
        {
            "key": "ai_success",
            "label": "AI 已处理",
            "count": session.scalar(
                select(func.count()).select_from(ArticleContent).where(ArticleContent.ai_status == "success")
            )
            or 0,
        },
    ]

    source_health_breakdown = [
        {"key": "healthy", "label": "健康来源", "count": _count(session, Source, Source.last_crawl_status == "success")},
        {"key": "warning", "label": "部分成功", "count": _count(session, Source, Source.last_crawl_status == "partial_success")},
        {"key": "failed", "label": "失败来源", "count": _count(session, Source, Source.last_crawl_status == "failed")},
        {"key": "idle", "label": "未抓取", "count": _count(session, Source, Source.last_crawl_status.is_(None))},
    ]

    latest_report = session.scalar(select(DailyReport).order_by(DailyReport.report_date.desc(), DailyReport.id.desc()).limit(1))
    latest_article = session.scalar(select(Article).order_by(Article.created_at.desc(), Article.id.desc()).limit(1))
    latest_job = session.scalar(select(JobRun).order_by(JobRun.started_at.desc(), JobRun.id.desc()).limit(1))

    return {
        "connection": _build_connection_info(),
        "tables": table_stats,
        "metrics": {
            "total_rows": sum(item["count"] for item in table_stats),
            "article_count": _count(session, Article),
            "failed_articles": next(item["count"] for item in article_status_breakdown if item["key"] == "ai_failed"),
            "report_count": _count(session, DailyReport),
            "job_run_count": _count(session, JobRun),
        },
        "article_status_breakdown": article_status_breakdown,
        "source_health_breakdown": source_health_breakdown,
        "recent": {
            "latest_report_date": latest_report.report_date.isoformat() if latest_report else None,
            "latest_article_created_at": latest_article.created_at.isoformat() if latest_article else None,
            "latest_job_started_at": latest_job.started_at.isoformat() if latest_job else None,
        },
    }


def cleanup_old_job_runs(session: Session, keep_days: int) -> MaintenanceResult:
    if keep_days < 0:
        raise ValueError("保留天数不能小于 0")

    cutoff = datetime.utcnow() - timedelta(days=keep_days)
    jobs = list(
        session.scalars(
            select(JobRun).where(
                JobRun.finished_at.is_not(None),
                JobRun.finished_at < cutoff,
            )
        )
    )

    for job in jobs:
        session.delete(job)

    session.commit()
    return MaintenanceResult(
        action="cleanup_old_job_runs",
        deleted_count=len(jobs),
        message=f"已清理 {len(jobs)} 条早于 {keep_days} 天的历史任务日志。",
        extra={"keep_days": keep_days},
    )


def cleanup_failed_articles(session: Session) -> MaintenanceResult:
    failed_article_ids = list(
        session.scalars(
            select(Article.id)
            .join(ArticleContent, ArticleContent.article_id == Article.id, isouter=True)
            .where(or_(Article.status == "failed", ArticleContent.ai_status == "failed"))
        )
    )

    if not failed_article_ids:
        return MaintenanceResult(
            action="cleanup_failed_articles",
            deleted_count=0,
            message="没有可清理的失败文章。",
        )

    affected_report_ids = list(
        session.scalars(
            select(DailyReportItem.report_id)
            .where(DailyReportItem.article_id.in_(failed_article_ids))
            .distinct()
        )
    )

    report_item_count = (
        session.query(DailyReportItem)
        .filter(DailyReportItem.article_id.in_(failed_article_ids))
        .delete(synchronize_session=False)
    )
    content_count = (
        session.query(ArticleContent)
        .filter(ArticleContent.article_id.in_(failed_article_ids))
        .delete(synchronize_session=False)
    )
    article_count = session.query(Article).filter(Article.id.in_(failed_article_ids)).delete(synchronize_session=False)
    _refresh_reports(session, affected_report_ids)
    session.commit()

    return MaintenanceResult(
        action="cleanup_failed_articles",
        deleted_count=article_count,
        message=f"已清理 {article_count} 篇失败文章，并同步删除关联内容与日报条目。",
        extra={
            "deleted_content_count": content_count,
            "deleted_report_item_count": report_item_count,
        },
    )


def delete_report_record(session: Session, report_id: int) -> MaintenanceResult:
    report = session.get(DailyReport, report_id)
    if report is None:
        raise ValueError("日报不存在")

    report_date = report.report_date.isoformat()
    removed_html = False

    if report.html_path:
        report_path = Path(report.html_path)
        if report_path.exists():
            report_path.unlink()
            removed_html = True

    session.delete(report)
    session.commit()

    return MaintenanceResult(
        action="delete_report_record",
        deleted_count=1,
        message=f"已删除 {report_date} 的日报记录。",
        extra={
            "report_date": report_date,
            "removed_html": removed_html,
        },
    )


def _build_table_stat(
    session: Session,
    model,
    key: str,
    label: str,
    description: str,
    last_updated_column=None,
) -> dict:
    last_value = None
    if last_updated_column is not None:
        last_value = session.scalar(select(func.max(last_updated_column)))

    return {
        "key": key,
        "label": label,
        "description": description,
        "count": _count(session, model),
        "last_updated_at": last_value.isoformat() if last_value else None,
    }


def _count(session: Session, model, *filters) -> int:
    statement = select(func.count()).select_from(model)
    if filters:
        statement = statement.where(*filters)
    return session.scalar(statement) or 0


def _build_connection_info() -> dict:
    database_url = get_settings().database_url
    parsed = make_url(database_url)
    database_name = str(parsed.database or "")
    if parsed.drivername.startswith("sqlite"):
        database_name = database_name or "本地 SQLite"

    return {
        "dialect": parsed.get_backend_name(),
        "driver": parsed.drivername,
        "database": database_name,
        "masked_url": _mask_database_url(parsed.render_as_string(hide_password=False)),
    }


def _mask_database_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url

    prefix, suffix = url.split("://", maxsplit=1)
    if "@" not in suffix:
        return url

    auth, host = suffix.split("@", maxsplit=1)
    if ":" not in auth:
        return f"{prefix}://***@{host}"

    username, _password = auth.split(":", maxsplit=1)
    return f"{prefix}://{username}:***@{host}"


def _refresh_reports(session: Session, report_ids: list[int]) -> None:
    if not report_ids:
        return

    reports = list(session.scalars(select(DailyReport).where(DailyReport.id.in_(report_ids))))
    for report in reports:
        items = list(session.scalars(select(DailyReportItem).where(DailyReportItem.report_id == report.id)))
        article_ids = [item.article_id for item in items]
        report.article_count = len(article_ids)
        if article_ids:
            report.source_count = (
                session.scalar(select(func.count(func.distinct(Article.source_id))).where(Article.id.in_(article_ids))) or 0
            )
        else:
            report.source_count = 0
        session.add(report)
