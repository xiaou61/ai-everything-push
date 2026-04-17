from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.db.models.article import Article
from app.db.models.job_run import JobRun
from app.db.models.report import DailyReport, DailyReportItem
from app.services.system_setting_service import get_setting_value


@dataclass
class ReportSummary:
    job_id: int
    report_id: int
    report_date: date
    article_count: int
    html_url: str


def generate_daily_report(session: Session, report_date: Optional[date] = None) -> ReportSummary:
    target_date = report_date or date.today()
    job = JobRun(
        job_name="generate_report_job",
        trigger_type="manual",
        status="running",
        started_at=datetime.utcnow(),
        processed_count=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    articles = list(
        session.scalars(
            select(Article)
            .options(joinedload(Article.source), joinedload(Article.content))
            .where(Article.status == "crawled")
            .order_by(Article.created_at.desc())
        ).unique()
    )
    selected = [article for article in articles if _article_matches_date(article, target_date) and _is_ready(article)]
    max_items = _get_max_articles_per_day(session)
    selected = selected[:max_items]

    report = session.scalar(select(DailyReport).where(DailyReport.report_date == target_date))
    if report is None:
        report = DailyReport(
            report_date=target_date,
            title=f"{target_date.isoformat()} 技术日报",
            intro=f"今天共整理 {len(selected)} 篇技术文章。",
            status="published",
            source_count=len({article.source_id for article in selected}),
            article_count=len(selected),
            feishu_pushed=False,
        )
        session.add(report)
        session.commit()
        session.refresh(report)
    else:
        for item in list(report.items):
            session.delete(item)
        report.title = f"{target_date.isoformat()} 技术日报"
        report.intro = f"今天共整理 {len(selected)} 篇技术文章。"
        report.status = "published"
        report.source_count = len({article.source_id for article in selected})
        report.article_count = len(selected)
        session.add(report)
        session.commit()
        session.refresh(report)

    for order, article in enumerate(selected, start=1):
        section_name = article.content.category if article.content and article.content.category else "技术观察"
        session.add(
            DailyReportItem(
                report_id=report.id,
                article_id=article.id,
                display_order=order,
                section_name=section_name,
            )
        )
    session.commit()
    session.refresh(report)

    html_url, html_path = _render_and_save_report(session, report)
    report.html_url = html_url
    report.html_path = html_path
    session.add(report)
    session.commit()

    job.status = "success"
    job.finished_at = datetime.utcnow()
    job.processed_count = len(selected)
    session.add(job)
    session.commit()

    return ReportSummary(
        job_id=job.id,
        report_id=report.id,
        report_date=target_date,
        article_count=len(selected),
        html_url=html_url,
    )


def list_reports(session: Session) -> list[DailyReport]:
    return list(session.scalars(select(DailyReport).order_by(DailyReport.report_date.desc())))


def get_report_by_date(session: Session, report_date: date) -> Optional[DailyReport]:
    statement = (
        select(DailyReport)
        .options(joinedload(DailyReport.items).joinedload(DailyReportItem.article).joinedload(Article.content), joinedload(DailyReport.items).joinedload(DailyReportItem.article).joinedload(Article.source))
        .where(DailyReport.report_date == report_date)
        .limit(1)
    )
    return session.scalar(statement)


def build_report_sections(report: DailyReport) -> dict[str, list[DailyReportItem]]:
    sections: dict[str, list[DailyReportItem]] = defaultdict(list)
    for item in sorted(report.items, key=lambda current: current.display_order):
        sections[item.section_name or "技术观察"].append(item)
    return dict(sections)


def _render_and_save_report(session: Session, report: DailyReport) -> tuple[str, str]:
    report = get_report_by_date(session, report.report_date) or report
    settings = get_settings()
    report_dir = Path("docs/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{report.report_date.isoformat()}.html"

    env = Environment(
        loader=FileSystemLoader("app/templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("reports/public.html")
    html = template.render(report=report, sections=build_report_sections(report), generated_at=datetime.utcnow())
    report_path.write_text(html, encoding="utf-8")

    return f"{settings.site_base_url}/daily/{report.report_date.isoformat()}", str(report_path).replace("\\", "/")


def _article_matches_date(article: Article, target_date: date) -> bool:
    article_date = article.published_at.date() if article.published_at else article.created_at.date()
    return article_date == target_date


def _is_ready(article: Article) -> bool:
    return article.content is not None and article.content.ai_status == "success"


def _get_max_articles_per_day(session: Session) -> int:
    value = get_setting_value(session, "report.max_articles_per_day", "30")
    try:
        return max(1, int(value or "30"))
    except ValueError:
        return 30
