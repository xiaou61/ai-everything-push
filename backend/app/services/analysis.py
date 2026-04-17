from __future__ import annotations

import re
from datetime import date


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "AI": (
        "ai",
        "agent",
        "llm",
        "gpt",
        "openai",
        "claude",
        "gemini",
        "模型",
        "推理",
        "智能体",
    ),
    "Engineering": (
        "framework",
        "deploy",
        "release",
        "github",
        "api",
        "backend",
        "frontend",
        "infra",
        "工程",
        "架构",
        "部署",
    ),
    "Product": (
        "launch",
        "roadmap",
        "design",
        "ux",
        "增长",
        "产品",
        "运营",
        "发布",
    ),
    "Security": (
        "security",
        "privacy",
        "漏洞",
        "攻击",
        "安全",
    ),
    "Policy": (
        "regulation",
        "policy",
        "compliance",
        "监管",
        "政策",
        "法案",
    ),
    "Funding": (
        "funding",
        "revenue",
        "acquisition",
        "融资",
        "营收",
        "收购",
    ),
}


class ContentAnalysisService:
    def classify(self, title: str, content: str, category_hint: str | None = None) -> str:
        if category_hint:
            return category_hint.strip()

        merged = f"{title} {content}".lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in merged for keyword in keywords):
                return category
        return "General"

    def summarize(self, title: str, content: str) -> str:
        clean_text = re.sub(r"\s+", " ", content).strip()
        if not clean_text:
            return title.strip()

        sentences = re.split(r"(?<=[。！？.!?])\s+", clean_text)
        selected = " ".join(item for item in sentences[:2] if item).strip()
        if not selected:
            selected = clean_text[:120]
        if len(selected) > 160:
            selected = f"{selected[:157].rstrip()}..."
        return selected

    def build_overview(self, digest_date: date, sections: list[dict], article_count: int) -> str:
        if article_count == 0:
            return f"{digest_date.isoformat()} 暂无可汇总内容。"

        lead_sections = sections[:3]
        top_descriptions = [f"{section['category']} {section['count']} 条" for section in lead_sections]
        summary_text = "，".join(top_descriptions)
        return (
            f"{digest_date.isoformat()} 共收录 {article_count} 条信息，"
            f"重点关注 {summary_text}。页面已按分类整理，可继续查看详细条目。"
        )

