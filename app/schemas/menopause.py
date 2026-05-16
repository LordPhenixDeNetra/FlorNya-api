from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MenopauseLogCreate(BaseModel):
    log_date: date
    hot_flash_count: int | None = Field(default=None, ge=0)
    night_sweats: bool | None = None
    vaginal_dryness: bool | None = None
    insomnia: bool | None = None
    mood_swings: bool | None = None
    weight_gain: bool | None = None
    brain_fog: bool | None = None
    joint_pain: bool | None = None
    severity: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=5000)


class MenopauseLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    hot_flash_count: int | None
    night_sweats: bool | None
    vaginal_dryness: bool | None
    insomnia: bool | None
    mood_swings: bool | None
    weight_gain: bool | None
    brain_fog: bool | None
    joint_pain: bool | None
    severity: int | None
    notes: str | None
    created_at: datetime


class HotFlashQuickLog(BaseModel):
    log_date: date
    count: int = Field(ge=1, le=50)


class MenopauseInsightsResponse(BaseModel):
    generated_at: datetime
    insights_markdown: str
    avg_hot_flash_per_day: float | None
    most_common_symptoms: list[str]
    perimenopause_risk: str | None


class PerimenopauseScreening(BaseModel):
    age: int
    irregular_cycles: bool = False
    hot_flashes: bool = False
    night_sweats: bool = False
    vaginal_dryness: bool = False
    sleep_issues: bool = False
    mood_changes: bool = False
    brain_fog: bool = False


class PerimenopauseScreeningResult(BaseModel):
    risk_level: str
    detected_signs: list[str]
    recommendations: list[str]
    disclaimer: str = "Ce bilan indicatif ne remplace pas un avis médical."
