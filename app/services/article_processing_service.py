from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models.article import Article, ArticleContent
from app.db.models.job_run import JobRun
from app.services.article_service import get_article
from app.services.ai.language import detect_language
from app.services.ai.pipeline import classify_content, generate_display_title, summarize_content, translate_content


@dataclass
class ProcessSummary:
    job_id: int
    processed_count: int
    success_count: int
    failed_count: int
    errors: list[str]


@dataclass
class ReprocessSummary:
    job_id: int
    article_id: int
    status: str
    ai_status: str
    message: str


def process_pending_articles(session: Session) -> ProcessSummary:
    job = JobRun(
        job_name="process_articles_job",
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
            .options(joinedload(Article.content))
            .where(Article.status == "crawled")
            .order_by(Article.created_at.asc())
        ).unique()
    )

    processed_count = 0
    success_count = 0
    failed_count = 0
    errors: list[str] = []

    for article in articles:
        content = article.content
        if content is None:
            continue
        if content.ai_status == "success":
            continue

        success, error_message = _process_article(session, article)
        processed_count += 1
        if success:
            success_count += 1
        else:
            failed_count += 1
            errors.append(f"{article.title}: {error_message}")

    job.status = "success" if not errors else "partial_success"
    job.finished_at = datetime.utcnow()
    job.processed_count = processed_count
    job.error_message = "\n".join(errors) if errors else None
    session.add(job)
    session.commit()

    return ProcessSummary(
        job_id=job.id,
        processed_count=processed_count,
        success_count=success_count,
        failed_count=failed_count,
        errors=errors,
    )


def reprocess_article(session: Session, article_id: int) -> ReprocessSummary:
    article = get_article(session, article_id)
    if article is None:
        raise ValueError("文章不存在")

    content = article.content
    if content is None or not (content.clean_content or content.raw_content):
        raise ValueError("文章还没有可处理的正文内容")

    job = JobRun(
        job_name="reprocess_article_job",
        trigger_type="manual",
        status="running",
        started_at=datetime.utcnow(),
        processed_count=0,
        details_json=json.dumps({"article_id": article_id}, ensure_ascii=False),
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    success, error_message = _process_article(session, article, force=True)
    session.refresh(job)
    session.refresh(article)
    if article.content is not None:
        session.refresh(article.content)

    job.finished_at = datetime.utcnow()
    job.processed_count = 1
    job.status = "success" if success else "failed"
    job.error_message = None if success else error_message
    session.add(job)
    session.commit()

    return ReprocessSummary(
        job_id=job.id,
        article_id=article.id,
        status=article.status,
        ai_status=article.content.ai_status if article.content else "failed",
        message="文章已重新处理。" if success else f"文章重新处理失败：{error_message}",
    )


def _process_article(session: Session, article: Article, force: bool = False) -> tuple[bool, str | None]:
    content = article.content
    if content is None:
        return False, "正文内容不存在"
    if content.ai_status == "success" and not force:
        return True, None

    try:
        clean_text = content.clean_content or content.raw_content or ""
        detected_language = detect_language(f"{article.title}\n{clean_text[:2000]}")
        article.language = detected_language

        if detected_language == "en":
            working_text = translate_content(session, article.title, clean_text)
            content.translated_content = working_text
        else:
            working_text = clean_text
            content.translated_content = clean_text if detected_language == "zh" else content.translated_content

        summary_result = summarize_content(session, article.title, working_text)
        category = classify_content(session, article.title, working_text)
        display_title = generate_display_title(session, article.title, str(summary_result.get("summary") or ""))

        content.summary = str(summary_result.get("summary") or "")
        content.keywords_json = str(summary_result.get("highlights") or [])
        content.category = category
        content.generated_title = display_title
        content.ai_status = "success"
        content.ai_error = None
        content.processed_at = datetime.utcnow()
        article.status = "processed"
        session.add(article)
        session.add(content)
        session.commit()
        return True, None
    except Exception as exc:  # noqa: BLE001
        article.status = "failed"
        content.ai_status = "failed"
        content.ai_error = str(exc)
        content.processed_at = datetime.utcnow()
        session.add(article)
        session.add(content)
        session.commit()
        return False, str(exc)
