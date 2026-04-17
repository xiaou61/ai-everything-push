from datetime import date, datetime

from app.services.digest import ArticleSnapshot, DigestService


def test_build_daily_digest_groups_articles_by_category() -> None:
    service = DigestService()
    articles = [
        ArticleSnapshot(
            article_id=1,
            title="模型发布",
            original_title="Model release",
            url="https://example.com/1",
            category="AI",
            summary="总结 1",
            author="alice",
            language="en",
            content="这是文章 1 的正文内容。",
            original_content="This is article 1.",
            published_at=datetime(2026, 4, 17, 9, 0, 0),
            source_name="OpenAI Forum",
        ),
        ArticleSnapshot(
            article_id=2,
            title="工程效率",
            original_title="工程效率",
            url="https://example.com/2",
            category="Engineering",
            summary="总结 2",
            author="bob",
            language="zh",
            content="这是文章 2 的正文内容。",
            original_content="这是文章 2 的正文内容。",
            published_at=datetime(2026, 4, 17, 10, 0, 0),
            source_name="Hacker News",
        ),
        ArticleSnapshot(
            article_id=3,
            title="推理优化",
            original_title="Reasoning optimization",
            url="https://example.com/3",
            category="AI",
            summary="总结 3",
            author=None,
            language="en",
            content="这是文章 3 的正文内容。",
            original_content="This is article 3.",
            published_at=datetime(2026, 4, 17, 11, 0, 0),
            source_name="OpenAI Forum",
        ),
    ]

    digest = service.build_digest_payload(digest_date=date(2026, 4, 17), articles=articles)

    assert digest["digest_date"] == "2026-04-17"
    assert digest["article_count"] == 3
    assert len(digest["sections"]) == 2
    assert digest["sections"][0]["category"] == "AI"
    assert digest["sections"][0]["count"] == 2
    assert digest["sections"][1]["category"] == "Engineering"
    assert digest["sections"][0]["articles"][0]["article_id"] == 3
    assert digest["sections"][0]["articles"][0]["author"] is None
    assert digest["sections"][0]["articles"][1]["author"] == "alice"
    assert digest["sections"][0]["articles"][1]["language"] == "en"
    assert digest["sections"][0]["articles"][1]["content"] == "这是文章 1 的正文内容。"
    assert digest["sections"][0]["articles"][1]["original_content"] == "This is article 1."


def test_enrich_sections_backfills_legacy_digest_articles() -> None:
    service = DigestService()
    legacy_sections = [
        {
            "category": "AI",
            "count": 1,
            "articles": [
                {
                    "title": "模型发布",
                    "url": "https://example.com/1",
                    "source_name": "OpenAI Forum",
                    "summary": "旧摘要",
                    "published_at": "2026-04-17T09:00:00",
                }
            ],
        }
    ]
    articles = [
        ArticleSnapshot(
            article_id=1,
            title="模型发布",
            original_title="Model release",
            url="https://example.com/1",
            category="AI",
            summary="新摘要",
            author="alice",
            language="en",
            content="这是文章 1 的正文内容。",
            original_content="This is article 1.",
            published_at=datetime(2026, 4, 17, 9, 0, 0),
            source_name="OpenAI Forum",
        )
    ]

    enriched_sections = service.enrich_sections(legacy_sections, articles)

    assert enriched_sections[0]["articles"][0]["article_id"] == 1
    assert enriched_sections[0]["articles"][0]["original_title"] == "Model release"
    assert enriched_sections[0]["articles"][0]["author"] == "alice"
    assert enriched_sections[0]["articles"][0]["language"] == "en"
    assert enriched_sections[0]["articles"][0]["content"] == "这是文章 1 的正文内容。"
    assert enriched_sections[0]["articles"][0]["original_content"] == "This is article 1."
    assert enriched_sections[0]["articles"][0]["summary"] == "旧摘要"
