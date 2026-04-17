from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.article_processing_service import reprocess_article
from app.services.article_service import get_article

router = APIRouter(prefix="/admin/api/articles", tags=["articles"])


@router.get("/{article_id}")
def get_article_detail(article_id: int, session: Session = Depends(get_db_session)) -> dict:
    article = get_article(session, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    return _serialize_article_detail(article)


@router.post("/{article_id}/reprocess")
def post_reprocess_article(article_id: int, session: Session = Depends(get_db_session)) -> dict:
    article = get_article(session, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    try:
        result = reprocess_article(session, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    refreshed_article = get_article(session, article_id)
    if refreshed_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    return {
        "job_id": result.job_id,
        "article_id": result.article_id,
        "status": result.status,
        "ai_status": result.ai_status,
        "message": result.message,
        "article": _serialize_article_detail(refreshed_article),
    }


def _serialize_article_detail(article) -> dict:
    content = article.content
    source = article.source
    return {
        "id": article.id,
        "title": article.title,
        "canonical_url": article.canonical_url,
        "author": article.author,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "language": article.language,
        "status": article.status,
        "crawl_error": article.crawl_error,
        "source_id": article.source_id,
        "source_name": source.name if source else "",
        "source_slug": source.slug if source else "",
        "generated_title": content.generated_title if content else None,
        "summary": content.summary if content else None,
        "category": content.category if content else None,
        "has_content": bool(content and (content.clean_content or content.raw_content)),
        "raw_content": content.raw_content if content else None,
        "clean_content": content.clean_content if content else None,
        "translated_content": content.translated_content if content else None,
        "keywords_json": content.keywords_json if content else None,
        "ai_status": content.ai_status if content else None,
        "ai_error": content.ai_error if content else None,
        "processed_at": content.processed_at.isoformat() if content and content.processed_at else None,
    }
