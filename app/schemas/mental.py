from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import CursorPaginationParams


class MoodLogCreate(BaseModel):
    log_date: date
    mood_score: int = Field(ge=1, le=5)
    journal_text: str | None = Field(default=None, max_length=10000)


class MoodLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    mood_score: int
    journal_text: str | None
    created_at: datetime


class MoodFilterParams(CursorPaginationParams):
    period: str | None = Field(default="30d", pattern=r"^\d+[dwm]$")
    min_score: int | None = Field(default=None, ge=1, le=5)
