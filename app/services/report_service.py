from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import func, select
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


@dataclass
class ReportEditorItemUpdate:
    article_id: int
    id: Optional[int] = None
    section_name: str | None = None
    display_order: int | None = None


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
            .where(Article.status.in_(["crawled", "processed"]))
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


def get_report(session: Session, report_id: int) -> Optional[DailyReport]:
    statement = _build_report_detail_query().where(DailyReport.id == report_id).limit(1)
    return session.scalar(statement)


def get_report_by_date(session: Session, report_date: date) -> Optional[DailyReport]:
    statement = _build_report_detail_query().where(DailyReport.report_date == report_date).limit(1)
    return session.scalar(statement)


def update_report(
    session: Session,
    report_id: int,
    title: str,
    intro: str | None,
    items: list[ReportEditorItemUpdate],
) -> DailyReport:
    report = get_report(session, report_id)
    if report is None:
        raise ValueError("日报不存在")
    if not title.strip():
        raise ValueError("日报标题不能为空")

    existing_items = {item.id: item for item in report.items}
    existing_items_by_article = {item.article_id: item for item in report.items}
    seen_item_ids: set[int] = set()
    desired_article_ids: set[int] = set()

    for order, payload in enumerate(items, start=1):
        section_name = (payload.section_name or "").strip() or "技术观察"

        if payload.id is not None:
            item = existing_items.get(payload.id)
            if item is None:
                raise ValueError("存在不属于当前日报的条目")
            if payload.article_id != item.article_id:
                raise ValueError("日报条目与文章不匹配")
            if item.id in seen_item_ids or item.article_id in desired_article_ids:
                raise ValueError("日报内文章不能重复")

            seen_item_ids.add(item.id)
            desired_article_ids.add(item.article_id)
            item.display_order = order
            item.section_name = section_name
            session.add(item)
            continue

        if payload.article_id in desired_article_ids:
            raise ValueError("日报内文章不能重复")
        if payload.article_id in existing_items_by_article:
            raise ValueError("日报内文章不能重复")

        article = _get_ready_article_for_report(session, payload.article_id, report.report_date)
        if article is None:
            raise ValueError("文章不可加入当前日报")

        desired_article_ids.add(article.id)
        session.add(
            DailyReportItem(
                report_id=report.id,
                article_id=article.id,
                display_order=order,
                section_name=section_name,
            )
        )

    for item in list(report.items):
        if item.id not in seen_item_ids:
            session.delete(item)

    report.title = title.strip()
    report.intro = (intro or "").strip() or None
    session.flush()
    _refresh_report_counts(session, report)
    session.commit()
    return get_report(session, report_id) or report


def publish_report(session: Session, report_id: int) -> DailyReport:
    report = get_report(session, report_id)
    if report is None:
        raise ValueError("日报不存在")

    _refresh_report_counts(session, report)
    report.status = "published"
    html_url, html_path = _render_and_save_report(session, report)
    report.html_url = html_url
    report.html_path = html_path
    session.add(report)
    session.commit()
    return get_report(session, report_id) or report


def list_report_candidate_articles(session: Session, report: DailyReport, limit: int = 30) -> list[Article]:
    selected_article_ids = {item.article_id for item in report.items}
    articles = list(
        session.scalars(
            select(Article)
            .options(joinedload(Article.source), joinedload(Article.content))
            .order_by(Article.published_at.desc(), Article.created_at.desc())
        ).unique()
    )
    return [
        article
        for article in articles
        if article.id not in selected_article_ids and _article_matches_date(article, report.report_date) and _is_ready(article)
    ][:limit]


def build_report_sections(report: DailyReport) -> dict[str, list[DailyReportItem]]:
    sections: dict[str, list[DailyReportItem]] = defaultdict(list)
    for item in sorted(report.items, key=lambda current: current.display_order):
        sections[item.section_name or "技术观察"].append(item)
    return dict(sections)


def build_report_view_data(report: DailyReport) -> dict:
    sections_map = build_report_sections(report)
    section_cards: list[dict] = []
    highlights: list[dict] = []
    source_names: list[str] = []
    seen_sources: set[str] = set()

    for section_name, items in sections_map.items():
        section_cards.append(
            {
                "name": section_name,
                "count": len(items),
                "entries": items,
                "anchor": _slugify_section_name(section_name),
            }
        )

        for item in items:
            source_name = item.article.source.name if item.article.source else "未知来源"
            if source_name not in seen_sources:
                seen_sources.add(source_name)
                source_names.append(source_name)

            if len(highlights) >= 3:
                continue

            summary = item.article.content.summary if item.article.content and item.article.content.summary else "暂无摘要。"
            highlights.append(
                {
                    "title": item.article.content.generated_title if item.article.content and item.article.content.generated_title else item.article.title,
                    "summary": summary,
                    "source_name": source_name,
                    "url": item.article.canonical_url,
                }
            )

    return {
        "sections": section_cards,
        "highlights": highlights,
        "source_names": source_names,
        "hero_intro": report.intro or f"今天共整理 {report.article_count} 篇技术文章，适合快速扫完重点再挑深入阅读。",
    }


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
    html = template.render(
        report=report,
        sections=build_report_sections(report),
        report_view=build_report_view_data(report),
        generated_at=datetime.utcnow(),
    )
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


def _slugify_section_name(value: str) -> str:
    return "-".join(part for part in value.replace("/", " ").replace("_", " ").split() if part).lower() or "section"


def _build_report_detail_query():
    return select(DailyReport).options(
        joinedload(DailyReport.items).joinedload(DailyReportItem.article).joinedload(Article.content),
        joinedload(DailyReport.items).joinedload(DailyReportItem.article).joinedload(Article.source),
    )


def _refresh_report_counts(session: Session, report: DailyReport) -> None:
    item_rows = list(session.scalars(select(DailyReportItem).where(DailyReportItem.report_id == report.id)))
    article_ids = [item.article_id for item in item_rows]
    report.article_count = len(article_ids)

    if article_ids:
        report.source_count = (
            session.scalar(select(func.count(func.distinct(Article.source_id))).where(Article.id.in_(article_ids))) or 0
        )
    else:
        report.source_count = 0


def _get_ready_article_for_report(session: Session, article_id: int, report_date: date) -> Optional[Article]:
    article = session.scalar(
        select(Article)
        .options(joinedload(Article.source), joinedload(Article.content))
        .where(Article.id == article_id)
        .limit(1)
    )
    if article is None:
        return None
    if not _article_matches_date(article, report_date):
        return None
    if not _is_ready(article):
        return None
    return article
