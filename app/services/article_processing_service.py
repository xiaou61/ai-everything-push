from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models.article import Article, ArticleContent
from app.db.models.job_run import JobRun
from app.services.ai.language import detect_language
from app.services.ai.pipeline import classify_content, generate_display_title, summarize_content, translate_content


@dataclass
class ProcessSummary:
    job_id: int
    processed_count: int
    success_count: int
    failed_count: int
    errors: list[str]


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

        try:
            clean_text = content.clean_content or ""
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
            session.add(article)
            session.add(content)
            session.commit()

            processed_count += 1
            success_count += 1
        except Exception as exc:  # noqa: BLE001
            failed_count += 1
            processed_count += 1
            content.ai_status = "failed"
            content.ai_error = str(exc)
            session.add(content)
            session.commit()
            errors.append(f"{article.title}: {exc}")

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

