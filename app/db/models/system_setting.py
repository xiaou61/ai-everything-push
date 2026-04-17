from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    setting_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)
    # MySQL 不支持为 TEXT 字段声明空字符串默认值，这里只保留 Python 侧默认值。
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
