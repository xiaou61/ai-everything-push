from __future__ import annotations

from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.services.ai.client_factory import build_chat_model, get_default_model_for_task
from app.services.ai.json_utils import extract_json_object


def translate_content(session: Session, title: str, content: str) -> str:
    fallback = content
    prompt = {
        "system": "你是技术翻译助手。请把英文技术文章翻译成自然中文，保留专有名词，不要额外解释。",
        "user": f"标题：{title}\n\n正文：\n{content}\n\n请返回 JSON：{{\"translated_text\": \"...\"}}",
    }
    result = _invoke_json_task(session, "translation", prompt, fallback={"translated_text": fallback})
    return str(result.get("translated_text") or fallback)


def summarize_content(session: Session, title: str, content: str) -> dict[str, Any]:
    fallback = {
        "summary": _fallback_summary(content),
        "highlights": _fallback_highlights(content),
    }
    prompt = {
        "system": "你是技术内容编辑，请将内容整理成中文日报摘要。",
        "user": (
            f"标题：{title}\n\n正文：\n{content}\n\n"
            "请返回 JSON：{\"summary\": \"一段总结\", \"highlights\": [\"要点1\", \"要点2\", \"要点3\"]}"
        ),
    }
    return _invoke_json_task(session, "summary", prompt, fallback=fallback)


def classify_content(session: Session, title: str, content: str) -> str:
    fallback = _fallback_category(title, content)
    prompt = {
        "system": "你是技术内容分类助手，请将文章归类到一个技术类别。",
        "user": (
            f"标题：{title}\n\n正文：\n{content}\n\n"
            "请返回 JSON：{\"category\": \"AI 平台\"}。类别尽量简短。"
        ),
    }
    result = _invoke_json_task(session, "classification", prompt, fallback={"category": fallback})
    return str(result.get("category") or fallback)


def generate_display_title(session: Session, title: str, summary: str) -> str:
    fallback = title
    prompt = {
        "system": "你是技术日报标题编辑，请把标题改写成适合中文日报展示的标题。",
        "user": (
            f"原标题：{title}\n\n摘要：\n{summary}\n\n"
            "请返回 JSON：{\"title\": \"新的中文标题\"}"
        ),
    }
    result = _invoke_json_task(session, "title", prompt, fallback={"title": fallback})
    return str(result.get("title") or fallback)


def _invoke_json_task(session: Session, task_type: str, prompt: dict[str, str], fallback: dict[str, Any]) -> dict[str, Any]:
    config = get_default_model_for_task(session, task_type)
    model = build_chat_model(config)
    if model is None:
        return fallback

    response = model.invoke(
        [
            SystemMessage(content=prompt["system"]),
            HumanMessage(content=prompt["user"]),
        ]
    )
    data = extract_json_object(getattr(response, "content", "") or "")
    return data or fallback


def _fallback_summary(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return "暂无摘要。"
    joined = " ".join(lines[:3])
    return joined[:180]


def _fallback_highlights(content: str) -> list[str]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return ["暂无要点"]
    highlights = lines[:3]
    return [line[:60] for line in highlights]


def _fallback_category(title: str, content: str) -> str:
    merged = f"{title}\n{content}".lower()
    if "model" in merged or "模型" in merged:
        return "模型工程"
    if "data" in merged or "数据" in merged:
        return "数据基础设施"
    if "frontend" in merged or "前端" in merged:
        return "前端工程"
    if "backend" in merged or "后端" in merged:
        return "后端架构"
    return "技术观察"

