from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Source
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate
from app.services.ingestion import IngestionService


router = APIRouter()


def _to_source_response(source: Source) -> SourceResponse:
    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        source_type=source.source_type,
        category_hint=source.category_hint,
        parser_config=source.parser_config,
        enabled=source.enabled,
        fetch_limit=source.fetch_limit,
        last_synced_at=source.last_synced_at.isoformat() if source.last_synced_at else None,
        created_at=source.created_at.isoformat(),
        updated_at=source.updated_at.isoformat(),
    )


@router.get("", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db)) -> list[SourceResponse]:
    sources = db.scalars(select(Source).order_by(Source.id.asc())).all()
    return [_to_source_response(item) for item in sources]


@router.post("", response_model=SourceResponse)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)) -> SourceResponse:
    source = Source(
        name=payload.name,
        url=str(payload.url),
        source_type=payload.source_type,
        category_hint=payload.category_hint,
        parser_config=payload.parser_config,
        enabled=payload.enabled,
        fetch_limit=payload.fetch_limit,
    )
    db.add(source)
    try:
        db.commit()
        db.refresh(source)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="数据源名称重复。") from error
    return _to_source_response(source)


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)) -> SourceResponse:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="数据源不存在。")

    updates = payload.model_dump(exclude_unset=True)
    for field_name, field_value in updates.items():
        if field_name == "url" and field_value is not None:
            setattr(source, field_name, str(field_value))
        else:
            setattr(source, field_name, field_value)
    source.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(source)
    return _to_source_response(source)


@router.post("/sync")
def sync_all_sources(db: Session = Depends(get_db)) -> dict:
    return IngestionService(db).sync_all_sources()


@router.post("/{source_id}/sync")
def sync_source(source_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return IngestionService(db).sync_source_by_id(source_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

