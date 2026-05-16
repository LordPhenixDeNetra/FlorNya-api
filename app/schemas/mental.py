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


# ── Emotional Journal ─────────────────────────────────────────────────────────

class EmotionalJournalCreate(BaseModel):
    log_date: date
    text: str = Field(max_length=20000)
    prompt_type: str = Field(default="free")
    mood_score_at_entry: int | None = Field(default=None, ge=1, le=5)


class EmotionalJournalPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    prompt_type: str
    prompt_text: str | None
    text: str | None
    mood_score_at_entry: int | None
    created_at: datetime


# ── Stress Techniques ─────────────────────────────────────────────────────────

class StressTechniquePublic(BaseModel):
    id: str
    name: str
    description: str
    duration_minutes: int
    phase_recommended: str | None
    category: str
    steps: list[str]


# ── Mood Correlation ──────────────────────────────────────────────────────────

class MoodPhaseCorrelation(BaseModel):
    phase: str
    average_mood: float
    entries_count: int


class MoodCorrelationResponse(BaseModel):
    period_days: int
    correlations: list[MoodPhaseCorrelation]
    best_phase: str | None
    worst_phase: str | None
    insights: str | None


# ── SPM / TDPM Detection ──────────────────────────────────────────────────────

class SPMDetectionResult(BaseModel):
    detected: bool
    severity: str
    pattern_days: int
    symptoms_correlation: list[str]
    recommendations: list[str]
    alert_level: str


# ── Mental Insights ───────────────────────────────────────────────────────────

class MentalInsightsResponse(BaseModel):
    generated_at: datetime
    insights_markdown: str
    average_mood_score: float | None
    mood_trend: str
    distress_days_detected: int
    recommendations: list[str]


# ── Mental Alert ──────────────────────────────────────────────────────────────

class MentalAlertPublic(BaseModel):
    id: UUID
    alert_type: str
    is_resolved: bool
    resources_sent: bool
    created_at: datetime


# ── Mental Resources ──────────────────────────────────────────────────────────

class MentalResourcePublic(BaseModel):
    category: str
    title: str
    description: str
    url: str | None
    phone: str | None
    country: str | None
