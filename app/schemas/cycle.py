import enum
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PaginationParams, SortOrder


class CyclePhase(str, enum.Enum):
    menstrual = "menstrual"
    follicular = "follicular"
    ovulatory = "ovulatory"
    luteal = "luteal"


class CycleRecordCreate(BaseModel):
    period_start: date
    cycle_length: int = Field(default=28, ge=15, le=60)
    notes: str | None = Field(default=None, max_length=5000)


class CycleRecordPublic(BaseModel):
    id: UUID
    user_id: UUID
    period_start: date
    cycle_length: int
    notes: str | None
    created_at: datetime


class CycleFilterParams(PaginationParams):
    date_from: date | None = None
    date_to: date | None = None
    sort_by: str = Field(default="period_start", pattern=r"^(period_start|cycle_length)$")
    order: SortOrder = SortOrder.desc


class FertileWindow(BaseModel):
    start: date
    end: date


class CurrentCycleResponse(BaseModel):
    phase: CyclePhase
    cycle_day: int
    last_period_start: date
    next_period_predicted: date
    fertile_window: FertileWindow
