from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Article
from app.schemas.article import ArticleResponse


router = APIRouter()


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)) -> ArticleResponse:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在。")

    return ArticleResponse(
        id=article.id,
        title=article.translated_title or article.title,
        original_title=article.title,
        url=article.url,
        source_name=article.source.name,
        category=article.category,
        summary=article.summary,
        author=article.author,
        language=article.language,
        content=article.translated_content or article.original_content,
        original_content=article.original_content,
        published_at=article.published_at.isoformat() if article.published_at else None,
        created_at=article.created_at.isoformat(),
        updated_at=article.updated_at.isoformat(),
        raw_payload=article.raw_payload,
    )
