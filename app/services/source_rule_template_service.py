from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.db.models.source import Source
from app.schemas.source_rule import SourceRuleUpsert


@dataclass
class SourceRuleTemplateResult:
    available: bool
    requires_rule: bool
    message: str
    payload: Optional[SourceRuleUpsert] = None


SOURCE_RULE_TEMPLATES: dict[str, SourceRuleUpsert] = {
    "anthropic-engineering": SourceRuleUpsert(
        list_item_selector="article",
        link_selector='a[href^="/engineering/"]',
        title_selector="h1",
        content_selector="article",
        remove_selectors="header, footer, nav, aside, script, style, form",
        request_headers_json='{"User-Agent":"Mozilla/5.0"}',
    ),
    "meituan-tech": SourceRuleUpsert(
        list_item_selector=".post-container",
        link_selector=".post-title a[href]",
        title_selector=".post-title, h1",
        content_selector="article, .post, .post-content, main",
        remove_selectors="header, footer, nav, aside, script, style, .copyright",
        request_headers_json='{"User-Agent":"Mozilla/5.0"}',
    ),
    "github-engineering": SourceRuleUpsert(
        list_item_selector="article",
        link_selector="h3 a[href]",
        title_selector="h1",
        content_selector="article",
        remove_selectors="header, footer, nav, aside, script, style, .newsletter-signup",
        request_headers_json='{"User-Agent":"Mozilla/5.0"}',
    ),
    "cloudflare-blog": SourceRuleUpsert(
        list_item_selector="article",
        link_selector="a[href]",
        title_selector="h1",
        content_selector="article, main",
        remove_selectors="header, footer, nav, aside, script, style, .newsletter-signup",
        request_headers_json='{"User-Agent":"Mozilla/5.0"}',
    ),
}


def get_rule_template_for_source(source: Source) -> SourceRuleTemplateResult:
    if source.source_type == "rss":
        return SourceRuleTemplateResult(
            available=False,
            requires_rule=False,
            message="RSS 来源默认不需要抓取规则，直接依赖 Feed 抓取即可。",
        )

    payload = SOURCE_RULE_TEMPLATES.get(source.slug)
    if payload is None:
        return SourceRuleTemplateResult(
            available=False,
            requires_rule=True,
            message="当前没有内置模板，请手工填写并通过预览调试。",
        )

    return SourceRuleTemplateResult(
        available=True,
        requires_rule=True,
        message="这是基于当前官网页面结构整理的推荐模板，建议先预览再保存。",
        payload=payload,
    )
