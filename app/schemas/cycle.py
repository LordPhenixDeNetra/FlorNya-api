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


class FlowIntensity(str, enum.Enum):
    spotting = "spotting"
    light = "light"
    medium = "medium"
    heavy = "heavy"


class CycleRecordCreate(BaseModel):
    period_start: date
    period_end: date | None = None
    cycle_length: int = Field(default=28, ge=15, le=60)
    flow_intensity: FlowIntensity | None = None
    notes: str | None = Field(default=None, max_length=5000)


class CycleRecordPublic(BaseModel):
    id: UUID
    user_id: UUID
    period_start: date
    period_end: date | None
    cycle_length: int
    flow_intensity: FlowIntensity | None
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


# ── Symptom log ──────────────────────────────────────────────────────────


class SymptomLogCreate(BaseModel):
    log_date: date
    cramps: bool | None = None
    bloating: bool | None = None
    breast_tenderness: bool | None = None
    headache: bool | None = None
    acne: bool | None = None
    fatigue: bool | None = None
    energy: int | None = Field(default=None, ge=1, le=5)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    libido: int | None = Field(default=None, ge=1, le=5)
    intensity: int | None = Field(default=None, ge=1, le=3)
    notes: str | None = Field(default=None, max_length=5000)


class SymptomLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    cramps: bool | None
    bloating: bool | None
    breast_tenderness: bool | None
    headache: bool | None
    acne: bool | None
    fatigue: bool | None
    energy: int | None
    sleep_quality: int | None
    libido: int | None
    intensity: int | None
    notes: str | None
    created_at: datetime


class SymptomFilterParams(BaseModel):
    date_from: date | None = None
    date_to: date | None = None


# ── Calendar ─────────────────────────────────────────────────────────────


class CalendarDay(BaseModel):
    date: date
    phase: CyclePhase | None
    cycle_day: int | None
    is_period: bool
    is_fertile: bool
    has_symptoms: bool
    has_mood: bool


class CalendarResponse(BaseModel):
    year: int
    month: int
    days: list[CalendarDay]


# ── AI Insights ───────────────────────────────────────────────────────────


class CycleInsightsResponse(BaseModel):
    generated_at: datetime
    insights_markdown: str
    cycle_regularity_score: float | None
    dominant_symptoms: list[str]
