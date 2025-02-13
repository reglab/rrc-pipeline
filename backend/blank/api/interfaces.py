from datetime import datetime

from pydantic import BaseModel, ConfigDict

from blank.db.models import PatternType


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProxyPatternCreate(ApiModel):
    pattern: str
    enabled: bool = True


class ProxyPatternRead(ApiModel):
    id: int
    pattern: str
    enabled: bool
    pattern_type: PatternType
    created_at: datetime
    updated_at: datetime


class ProxyPatternUpdate(ApiModel):
    pattern: str | None = None
    enabled: bool | None = None
