from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Article, DailyDigest
from app.services.analysis import ContentAnalysisService


@dataclass(slots=True)
class ArticleSnapshot:
    article_id: int
    title: str
    original_title: str
    url: str
    category: str
    summary: str
    author: str | None
    language: str
    content: str | None
    original_content: str | None
    published_at: datetime | None
    source_name: str


class DigestService:
    def __init__(self, analysis_service: ContentAnalysisService | None = None) -> None:
        self.analysis_service = analysis_service or ContentAnalysisService()

    def list_article_snapshots(self, db: Session, digest_date: date) -> list[ArticleSnapshot]:
        statement = (
            select(Article)
            .join(Article.source)
            .where(
                or_(
                    func.date(Article.published_at) == digest_date,
                    func.date(Article.created_at) == digest_date,
                )
            )
            .order_by(Article.published_at.desc(), Article.created_at.desc())
        )
        article_rows = db.scalars(statement).all()
        return [
            ArticleSnapshot(
                article_id=article.id,
                title=article.translated_title or article.title,
                original_title=article.title,
                url=article.url,
                category=article.category,
                summary=article.summary,
                author=article.author,
                language=article.language,
                content=article.translated_content or article.original_content,
                original_content=article.original_content,
                published_at=article.published_at,
                source_name=article.source.name,
            )
            for article in article_rows
        ]

    def build_digest_payload(self, digest_date: date, articles: list[ArticleSnapshot]) -> dict:
        grouped: dict[str, list[ArticleSnapshot]] = {}
        for article in articles:
            grouped.setdefault(article.category or "General", []).append(article)

        sections: list[dict] = []
        for category, items in grouped.items():
            ordered_items = sorted(
                items,
                key=lambda item: item.published_at or datetime.min,
                reverse=True,
            )
            sections.append(
                {
                    "category": category,
                    "count": len(ordered_items),
                    "articles": [
                        {
                            "article_id": item.article_id,
                            "title": item.title,
                            "original_title": item.original_title,
                            "url": item.url,
                            "summary": item.summary,
                            "author": item.author,
                            "language": item.language,
                            "content": item.content,
                            "original_content": item.original_content,
                            "published_at": item.published_at.isoformat() if item.published_at else None,
                            "source_name": item.source_name,
                        }
                        for item in ordered_items[:5]
                    ],
                }
            )

        ordered_sections = sorted(sections, key=lambda section: (-section["count"], section["category"]))
        return {
            "digest_date": digest_date.isoformat(),
            "headline": f"{digest_date.isoformat()} 论坛情报日报",
            "overview": self.analysis_service.build_overview(digest_date, ordered_sections, len(articles)),
            "article_count": len(articles),
            "section_count": len(ordered_sections),
            "sections": ordered_sections,
        }

    def enrich_sections(self, sections: list[dict], articles: list[ArticleSnapshot]) -> list[dict]:
        if not sections:
            return sections

        article_by_url = {article.url: article for article in articles}
        article_by_title = {article.title: article for article in articles}
        enriched_sections: list[dict] = []

        for section in sections:
            raw_articles = section.get("articles", []) if isinstance(section, Mapping) else []
            enriched_articles: list[dict] = []

            for raw_article in raw_articles:
                if not isinstance(raw_article, Mapping):
                    continue

                match = article_by_url.get(str(raw_article.get("url") or "")) or article_by_title.get(
                    str(raw_article.get("title") or "")
                )
                if match is None:
                    enriched_articles.append(dict(raw_article))
                    continue

                enriched_articles.append(
                    {
                        "article_id": raw_article.get("article_id", match.article_id),
                        "title": raw_article.get("title") or match.title,
                        "original_title": raw_article.get("original_title") or match.original_title,
                        "url": raw_article.get("url") or match.url,
                        "source_name": raw_article.get("source_name") or match.source_name,
                        "summary": raw_article.get("summary") or match.summary,
                        "author": raw_article.get("author") if raw_article.get("author") is not None else match.author,
                        "language": raw_article.get("language")
                        if raw_article.get("language") is not None
                        else match.language,
                        "content": raw_article.get("content") if raw_article.get("content") is not None else match.content,
                        "original_content": raw_article.get("original_content")
                        if raw_article.get("original_content") is not None
                        else match.original_content,
                        "published_at": raw_article.get("published_at")
                        or (match.published_at.isoformat() if match.published_at else None),
                    }
                )

            enriched_sections.append(
                {
                    "category": section.get("category", "General"),
                    "count": section.get("count", len(enriched_articles)),
                    "articles": enriched_articles,
                }
            )

        return enriched_sections

    def generate_digest(self, db: Session, digest_date: date) -> DailyDigest:
        snapshots = self.list_article_snapshots(db, digest_date)
        payload = self.build_digest_payload(digest_date=digest_date, articles=snapshots)

        digest = db.scalar(select(DailyDigest).where(DailyDigest.digest_date == digest_date))
        if digest is None:
            digest = DailyDigest(digest_date=digest_date, headline="", overview="", article_count=0, section_count=0, sections=[])
            db.add(digest)

        digest.headline = payload["headline"]
        digest.overview = payload["overview"]
        digest.article_count = payload["article_count"]
        digest.section_count = payload["section_count"]
        digest.sections = payload["sections"]

        db.commit()
        db.refresh(digest)
        return digest
