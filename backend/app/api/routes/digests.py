from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import DailyDigest
from app.schemas.digest import DigestResponse
from app.services.digest import DigestService
from app.services.feishu import FeishuService


router = APIRouter()


def _to_digest_response(digest: DailyDigest) -> DigestResponse:
    return DigestResponse(
        id=digest.id,
        digest_date=digest.digest_date.isoformat(),
        headline=digest.headline,
        overview=digest.overview,
        article_count=digest.article_count,
        section_count=digest.section_count,
        sections=digest.sections,
        pushed_at=digest.pushed_at.isoformat() if digest.pushed_at else None,
    )


@router.get("", response_model=list[DigestResponse])
def list_digests(db: Session = Depends(get_db)) -> list[DigestResponse]:
    digests = db.scalars(select(DailyDigest).order_by(DailyDigest.digest_date.desc())).all()
    return [_to_digest_response(item) for item in digests]


@router.get("/by-date/{digest_date}", response_model=DigestResponse)
def get_digest_by_date(digest_date: date, db: Session = Depends(get_db)) -> DigestResponse:
    digest = db.scalar(select(DailyDigest).where(DailyDigest.digest_date == digest_date))
    if digest is None:
        raise HTTPException(status_code=404, detail="日报不存在。")

    digest_service = DigestService()
    article_snapshots = digest_service.list_article_snapshots(db, digest_date)
    enriched_sections = digest_service.enrich_sections(digest.sections, article_snapshots)

    return DigestResponse(
        id=digest.id,
        digest_date=digest.digest_date.isoformat(),
        headline=digest.headline,
        overview=digest.overview,
        article_count=digest.article_count,
        section_count=digest.section_count,
        sections=enriched_sections,
        pushed_at=digest.pushed_at.isoformat() if digest.pushed_at else None,
    )


@router.post("/generate", response_model=DigestResponse)
def generate_digest(
    digest_date: date = Query(default_factory=lambda: datetime.now().date()),
    db: Session = Depends(get_db),
) -> DigestResponse:
    digest = DigestService().generate_digest(db, digest_date)
    return _to_digest_response(digest)


@router.post("/{digest_id}/push", response_model=DigestResponse)
def push_digest(digest_id: int, db: Session = Depends(get_db)) -> DigestResponse:
    digest = db.get(DailyDigest, digest_id)
    if digest is None:
        raise HTTPException(status_code=404, detail="日报不存在。")

    try:
        FeishuService().push_digest(digest)
        db.commit()
        db.refresh(digest)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"飞书推送失败：{error}") from error

    return _to_digest_response(digest)
