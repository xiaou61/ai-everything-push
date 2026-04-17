from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.model_config import ModelConfigCreate, ModelConfigRead, ModelConfigUpdate
from app.services.model_config_service import create_model_config, get_model_config, list_model_configs, update_model_config

router = APIRouter(prefix="/admin/api/models", tags=["models"])


@router.get("", response_model=list[ModelConfigRead])
def get_models(session: Session = Depends(get_db_session)):
    return list_model_configs(session)


@router.post("", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
def post_model(payload: ModelConfigCreate, session: Session = Depends(get_db_session)):
    return create_model_config(session, payload)


@router.put("/{config_id}", response_model=ModelConfigRead)
def put_model(config_id: int, payload: ModelConfigUpdate, session: Session = Depends(get_db_session)):
    record = get_model_config(session, config_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在")
    return update_model_config(session, record, payload)

