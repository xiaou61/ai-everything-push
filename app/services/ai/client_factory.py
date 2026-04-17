from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model_config import ModelConfig


def get_default_model_for_task(session: Session, task_type: str) -> Optional[ModelConfig]:
    statement = (
        select(ModelConfig)
        .where(
            ModelConfig.task_type == task_type,
            ModelConfig.enabled.is_(True),
            ModelConfig.is_default.is_(True),
        )
        .limit(1)
    )
    return session.scalar(statement)


def build_chat_model(config: Optional[ModelConfig]) -> Optional[ChatOpenAI]:
    if config is None:
        return None

    api_key = os.getenv(config.api_key_env_name, "").strip()
    if not api_key or not config.base_url:
        return None

    return ChatOpenAI(
        model=config.model_name,
        api_key=api_key,
        base_url=config.base_url,
        temperature=float(config.temperature),
        max_tokens=config.max_tokens,
    )

