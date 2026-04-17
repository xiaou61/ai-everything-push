from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate


def list_model_configs(session: Session) -> list[ModelConfig]:
    return list(session.scalars(select(ModelConfig).order_by(ModelConfig.task_type.asc(), ModelConfig.created_at.desc())))


def create_model_config(session: Session, payload: ModelConfigCreate) -> ModelConfig:
    if payload.is_default:
        _clear_default_for_task(session, payload.task_type)

    record = ModelConfig(**payload.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_model_config(session: Session, config_id: int) -> Optional[ModelConfig]:
    return session.get(ModelConfig, config_id)


def update_model_config(session: Session, record: ModelConfig, payload: ModelConfigUpdate) -> ModelConfig:
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default") and data.get("task_type"):
        _clear_default_for_task(session, data["task_type"])
    elif data.get("is_default"):
        _clear_default_for_task(session, record.task_type)

    for key, value in data.items():
        setattr(record, key, value)

    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def _clear_default_for_task(session: Session, task_type: str) -> None:
    records = session.scalars(select(ModelConfig).where(ModelConfig.task_type == task_type))
    for item in records:
        item.is_default = False
        session.add(item)
    session.flush()
