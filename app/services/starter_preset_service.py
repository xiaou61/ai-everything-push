from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model_config import ModelConfig
from app.db.models.source import Source

DEFAULT_SOURCE_PRESETS: list[dict[str, object]] = [
    {
        "name": "美团技术团队",
        "slug": "meituan-tech",
        "source_type": "web",
        "site_url": "https://tech.meituan.com/",
        "list_url": "https://tech.meituan.com/",
        "feed_url": None,
        "category": "国内技术博客",
        "language_hint": "zh",
        "enabled": True,
        "include_in_daily": True,
        "crawl_interval_minutes": 180,
    },
    {
        "name": "Anthropic Engineering",
        "slug": "anthropic-engineering",
        "source_type": "web",
        "site_url": "https://www.anthropic.com/engineering",
        "list_url": "https://www.anthropic.com/engineering",
        "feed_url": None,
        "category": "AI Engineering",
        "language_hint": "en",
        "enabled": True,
        "include_in_daily": True,
        "crawl_interval_minutes": 180,
    },
    {
        "name": "GitHub Engineering",
        "slug": "github-engineering",
        "source_type": "web",
        "site_url": "https://github.blog/engineering/",
        "list_url": "https://github.blog/engineering/",
        "feed_url": None,
        "category": "海外技术博客",
        "language_hint": "en",
        "enabled": True,
        "include_in_daily": True,
        "crawl_interval_minutes": 180,
    },
    {
        "name": "Cloudflare Blog",
        "slug": "cloudflare-blog",
        "source_type": "web",
        "site_url": "https://blog.cloudflare.com/",
        "list_url": "https://blog.cloudflare.com/",
        "feed_url": None,
        "category": "基础设施与云",
        "language_hint": "en",
        "enabled": True,
        "include_in_daily": True,
        "crawl_interval_minutes": 180,
    },
]

DEFAULT_MODEL_PRESETS: list[dict[str, object]] = [
    {
        "task_type": "translation",
        "provider_name": "aiwanwu",
        "model_name": "gpt-4.1-mini",
        "base_url": "https://www.aiwanwu.cc/v1",
        "api_key_env_name": "AIWANWU_API_KEY",
        "temperature": "0.2",
        "max_tokens": 4000,
        "enabled": True,
        "is_default": True,
    },
    {
        "task_type": "summary",
        "provider_name": "aiwanwu",
        "model_name": "gpt-4.1-mini",
        "base_url": "https://www.aiwanwu.cc/v1",
        "api_key_env_name": "AIWANWU_API_KEY",
        "temperature": "0.2",
        "max_tokens": 4000,
        "enabled": True,
        "is_default": True,
    },
    {
        "task_type": "classification",
        "provider_name": "aiwanwu",
        "model_name": "gpt-4.1-mini",
        "base_url": "https://www.aiwanwu.cc/v1",
        "api_key_env_name": "AIWANWU_API_KEY",
        "temperature": "0.1",
        "max_tokens": 2000,
        "enabled": True,
        "is_default": True,
    },
    {
        "task_type": "title",
        "provider_name": "aiwanwu",
        "model_name": "gpt-4.1-mini",
        "base_url": "https://www.aiwanwu.cc/v1",
        "api_key_env_name": "AIWANWU_API_KEY",
        "temperature": "0.3",
        "max_tokens": 2000,
        "enabled": True,
        "is_default": True,
    },
]


def get_starter_overview(session: Session) -> dict:
    existing_source_slugs = set(session.scalars(select(Source.slug)))
    existing_model_tasks = set(session.scalars(select(ModelConfig.task_type)))

    sources = [
        {
            **item,
            "exists": item["slug"] in existing_source_slugs,
        }
        for item in DEFAULT_SOURCE_PRESETS
    ]
    models = [
        {
            **item,
            "exists": item["task_type"] in existing_model_tasks,
        }
        for item in DEFAULT_MODEL_PRESETS
    ]

    return {
        "sources": sources,
        "models": models,
        "missing_source_count": sum(1 for item in sources if not item["exists"]),
        "missing_model_count": sum(1 for item in models if not item["exists"]),
    }


def apply_starter_presets(session: Session) -> dict:
    existing_source_slugs = set(session.scalars(select(Source.slug)))
    existing_model_tasks = set(session.scalars(select(ModelConfig.task_type)))

    created_sources: list[str] = []
    created_models: list[str] = []
    skipped_sources: list[str] = []
    skipped_models: list[str] = []

    for item in DEFAULT_SOURCE_PRESETS:
        slug = str(item["slug"])
        if slug in existing_source_slugs:
            skipped_sources.append(slug)
            continue

        session.add(Source(**item))
        created_sources.append(slug)

    for item in DEFAULT_MODEL_PRESETS:
        task_type = str(item["task_type"])
        if task_type in existing_model_tasks:
            skipped_models.append(task_type)
            continue

        session.add(ModelConfig(**item))
        created_models.append(task_type)

    session.commit()

    return {
        "created_sources": created_sources,
        "created_models": created_models,
        "skipped_sources": skipped_sources,
        "skipped_models": skipped_models,
        "overview": get_starter_overview(session),
    }
