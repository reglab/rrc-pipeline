from __future__ import annotations

import datetime
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class PatternType(StrEnum):
    NAME = "regex"
    URL = "url"


class ProxyPattern(Base, TimestampMixin):
    __tablename__ = "proxy_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    pattern: Mapped[str] = mapped_column(unique=True)
    enabled: Mapped[bool] = mapped_column(server_default=sa.text("true"))
    pattern_type: Mapped[PatternType] = mapped_column(server_default=PatternType.NAME)
