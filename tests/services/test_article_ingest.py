from __future__ import annotations

from app.core.database import SessionLocal
from app.db.models.source import Source
from app.services.article_ingest_service import ArticlePayload, create_or_update_article


def test_duplicate_article_is_skipped():
    session = SessionLocal()
    try:
        source = Source(
            name="Test Source",
            slug="test-source",
            site_url="https://example.com",
            source_type="rss",
            feed_url="https://example.com/feed.xml",
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        first, first_created = create_or_update_article(
            session,
            source,
            ArticlePayload(
                title="Example",
                canonical_url="https://example.com/a",
                clean_content="content",
            ),
        )
        second, second_created = create_or_update_article(
            session,
            source,
            ArticlePayload(
                title="Example",
                canonical_url="https://example.com/a",
                clean_content="content",
            ),
        )

        assert first_created is True
        assert second_created is False
        assert first.id == second.id
    finally:
        session.close()

