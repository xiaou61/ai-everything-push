from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ModelConfig(TimestampMixin, Base):
    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key_env_name: Mapped[str] = mapped_column(String(255), nullable=False)
    temperature: Mapped[str] = mapped_column(String(32), nullable=False, default="0.2", server_default="0.2")
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=4000, server_default="4000")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

