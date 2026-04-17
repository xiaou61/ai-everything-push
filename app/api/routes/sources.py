from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.source import SourceCreate, SourceRead, SourceUpdate
from app.services.source_health_service import serialize_source
from app.services.source_service import create_source, get_source, list_sources, toggle_source, update_source

router = APIRouter(prefix="/admin/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
def get_sources(session: Session = Depends(get_db_session)):
    return [serialize_source(item) for item in list_sources(session)]


@router.get("/{source_id}", response_model=SourceRead)
def get_source_detail(source_id: int, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")
    return serialize_source(source)


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def post_source(payload: SourceCreate, session: Session = Depends(get_db_session)):
    return serialize_source(create_source(session, payload))


@router.put("/{source_id}", response_model=SourceRead)
def put_source(source_id: int, payload: SourceUpdate, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")
    return serialize_source(update_source(session, source, payload))


@router.post("/{source_id}/toggle", response_model=SourceRead)
def post_toggle_source(source_id: int, session: Session = Depends(get_db_session)):
    source = get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在")
    return serialize_source(toggle_source(session, source))
