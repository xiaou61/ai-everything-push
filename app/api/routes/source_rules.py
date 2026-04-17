from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.form_utils import parse_simple_form
from app.core.templating import templates
from app.schemas.source_rule import SourceRuleRead, SourceRuleUpsert
from app.services.source_rule_preview_service import preview_source_rule
from app.services.source_rule_service import get_rule_by_source, upsert_source_rule
from app.services.source_service import get_source

router = APIRouter(tags=["source-rules"])


@router.get("/admin/sources/{source_id}/rules", response_class=HTMLResponse)
def admin_source_rules(source_id: int, request: Request, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")

    rule = get_rule_by_source(session, source_id)
    return templates.TemplateResponse(
        request=request,
        name="sources/rules.html",
        context={
            "source": source,
            "rule": rule,
            "rule_form": _rule_form_data(rule),
            "preview": None,
            "preview_url": "",
            "title": f"{source.name} 抓取规则",
        },
    )


@router.post("/admin/sources/{source_id}/rules/save")
async def save_source_rules_from_form(source_id: int, request: Request, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")

    form = parse_simple_form(await request.body())
    payload = _build_rule_payload(form)
    upsert_source_rule(session, source, payload)
    return RedirectResponse(url=f"/admin/sources/{source_id}/rules", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/sources/{source_id}/rules/preview", response_class=HTMLResponse)
async def preview_source_rules_from_form(source_id: int, request: Request, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")

    form = parse_simple_form(await request.body())
    payload = _build_rule_payload(form)
    preview_url = form.get("preview_url", "").strip()
    preview_mode = form.get("preview_mode", "list").strip() or "list"

    preview = None
    preview_error = ""
    try:
        preview = preview_source_rule(source, payload, preview_mode, preview_url or None)
    except Exception as exc:  # noqa: BLE001
        preview_error = str(exc)

    return templates.TemplateResponse(
        request=request,
        name="sources/rules.html",
        context={
            "source": source,
            "rule": get_rule_by_source(session, source_id),
            "rule_form": _rule_form_data(payload),
            "preview": preview,
            "preview_error": preview_error,
            "preview_url": preview_url,
            "title": f"{source.name} 抓取规则",
        },
    )


@router.get("/admin/api/sources/{source_id}/rules", response_model=Optional[SourceRuleRead])
def get_source_rules(source_id: int, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")
    return get_rule_by_source(session, source_id)


@router.post("/admin/api/sources/{source_id}/rules", response_model=SourceRuleRead, status_code=status.HTTP_201_CREATED)
def post_source_rules(source_id: int, payload: SourceRuleUpsert, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")
    return upsert_source_rule(session, source, payload)


@router.post("/admin/api/sources/{source_id}/rules/preview")
def post_source_rule_preview(source_id: int, payload: dict, session: Session = Depends(get_db_session)) -> dict:
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")

    preview_mode = str(payload.get("preview_mode", "list"))
    preview_url = str(payload.get("preview_url", "")).strip() or None
    rule_payload = SourceRuleUpsert(
        list_item_selector=str(payload.get("list_item_selector", "")).strip() or None,
        link_selector=str(payload.get("link_selector", "")).strip() or None,
        title_selector=str(payload.get("title_selector", "")).strip() or None,
        published_at_selector=str(payload.get("published_at_selector", "")).strip() or None,
        author_selector=str(payload.get("author_selector", "")).strip() or None,
        content_selector=str(payload.get("content_selector", "")).strip() or None,
        remove_selectors=str(payload.get("remove_selectors", "")).strip() or None,
        request_headers_json=str(payload.get("request_headers_json", "")).strip() or None,
    )
    result = preview_source_rule(source, rule_payload, preview_mode, preview_url)
    return {
        "mode": result.mode,
        "source_type": result.source_type,
        "request_url": result.request_url,
        "article_url": result.article_url,
        "items": result.items or [],
        "extracted_text": result.extracted_text,
        "extracted_length": result.extracted_length,
    }


def _build_rule_payload(form: dict[str, str]) -> SourceRuleUpsert:
    return SourceRuleUpsert(
        list_item_selector=form.get("list_item_selector", "").strip() or None,
        link_selector=form.get("link_selector", "").strip() or None,
        title_selector=form.get("title_selector", "").strip() or None,
        published_at_selector=form.get("published_at_selector", "").strip() or None,
        author_selector=form.get("author_selector", "").strip() or None,
        content_selector=form.get("content_selector", "").strip() or None,
        remove_selectors=form.get("remove_selectors", "").strip() or None,
        request_headers_json=form.get("request_headers_json", "").strip() or None,
    )


def _rule_form_data(rule: Optional[object]) -> dict[str, str]:
    if rule is None:
        return {
            "list_item_selector": "",
            "link_selector": "",
            "title_selector": "",
            "published_at_selector": "",
            "author_selector": "",
            "content_selector": "",
            "remove_selectors": "",
            "request_headers_json": "",
        }

    return {
        "list_item_selector": getattr(rule, "list_item_selector", "") or "",
        "link_selector": getattr(rule, "link_selector", "") or "",
        "title_selector": getattr(rule, "title_selector", "") or "",
        "published_at_selector": getattr(rule, "published_at_selector", "") or "",
        "author_selector": getattr(rule, "author_selector", "") or "",
        "content_selector": getattr(rule, "content_selector", "") or "",
        "remove_selectors": getattr(rule, "remove_selectors", "") or "",
        "request_headers_json": getattr(rule, "request_headers_json", "") or "",
    }
