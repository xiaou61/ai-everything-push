from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Article, Source
from app.services.analysis import ContentAnalysisService
from app.services.language import LanguageService
from app.services.parsers import ParsedEntry, SourceParserService
from app.services.translation import TranslationService


class IngestionService:
    def __init__(
        self,
        db: Session,
        parser_service: SourceParserService | None = None,
        language_service: LanguageService | None = None,
        translation_service: TranslationService | None = None,
        analysis_service: ContentAnalysisService | None = None,
    ) -> None:
        self.db = db
        self.parser_service = parser_service or SourceParserService()
        self.language_service = language_service or LanguageService()
        self.translation_service = translation_service or TranslationService()
        self.analysis_service = analysis_service or ContentAnalysisService()

    def sync_all_sources(self) -> dict:
        sources = self.db.scalars(select(Source).where(Source.enabled.is_(True)).order_by(Source.id.asc())).all()
        results = [self.sync_source(source) for source in sources]
        return {
            "source_count": len(results),
            "new_articles": sum(item["new_articles"] for item in results),
            "results": results,
        }

    def sync_source_by_id(self, source_id: int) -> dict:
        source = self.db.get(Source, source_id)
        if source is None:
            raise ValueError("数据源不存在。")
        return self.sync_source(source)

    def sync_source(self, source: Source) -> dict:
        items = self.parser_service.fetch(source)
        created_count = 0

        for item in items:
            if self._article_exists(source.id, item.external_id):
                continue

            language = self.language_service.detect_language(f"{item.title} {item.content}")
            translated_title = self.translation_service.translate_to_chinese(item.title, language) if self.language_service.needs_translation(language) else item.title
            translated_content = (
                self.translation_service.translate_to_chinese(item.content, language)
                if item.content and self.language_service.needs_translation(language)
                else item.content
            )
            normalized_text = (translated_content or item.content or item.title).strip()
            category = self.analysis_service.classify(translated_title, normalized_text, source.category_hint)
            summary = self.analysis_service.summarize(translated_title, normalized_text)

            article = Article(
                source_id=source.id,
                external_id=item.external_id,
                title=item.title,
                translated_title=translated_title if translated_title != item.title else None,
                url=item.url,
                author=item.author,
                published_at=item.published_at,
                language=language,
                original_content=item.content or None,
                translated_content=translated_content if translated_content != item.content else None,
                category=category,
                summary=summary,
                raw_payload=item.raw_payload,
            )
            self.db.add(article)
            created_count += 1

        source.last_synced_at = datetime.utcnow()
        self.db.commit()
        return {
            "source_id": source.id,
            "source_name": source.name,
            "new_articles": created_count,
            "fetched_items": len(items),
        }

    def _article_exists(self, source_id: int, external_id: str) -> bool:
        statement = select(Article.id).where(Article.source_id == source_id, Article.external_id == external_id)
        return self.db.scalar(statement) is not None

