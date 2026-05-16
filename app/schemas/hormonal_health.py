import enum
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TreatmentType(str, enum.Enum):
    pill = "pill"
    patch = "patch"
    iud = "iud"
    implant = "implant"
    injection = "injection"
    ring = "ring"
    other = "other"


class PainLogCreate(BaseModel):
    log_date: date
    pain_intensity: int | None = Field(default=None, ge=1, le=10)
    pelvic: bool | None = None
    lower_back: bool | None = None
    dysmenorrhea: bool | None = None
    dyspareunia: bool | None = None
    bloating: bool | None = None
    body_zones: list[str] | None = None
    notes: str | None = Field(default=None, max_length=5000)


class PainLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    pain_intensity: int | None
    pelvic: bool | None
    lower_back: bool | None
    dysmenorrhea: bool | None
    dyspareunia: bool | None
    bloating: bool | None
    body_zones: list[str] | None
    notes: str | None
    created_at: datetime


class HormonalTreatmentCreate(BaseModel):
    treatment_type: TreatmentType
    brand_name: str | None = Field(default=None, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    reminder_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    side_effects: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=5000)


class HormonalTreatmentPublic(BaseModel):
    id: UUID
    user_id: UUID
    treatment_type: TreatmentType
    brand_name: str | None
    start_date: date | None
    end_date: date | None
    is_active: bool
    reminder_time: str | None
    side_effects: str | None
    notes: str | None
    created_at: datetime


class PCOSRiskAssessment(BaseModel):
    irregular_cycles: bool = False
    excess_hair_growth: bool = False
    acne: bool = False
    weight_gain: bool = False
    hair_loss: bool = False
    difficulty_conceiving: bool = False
    mood_swings: bool = False
    fatigue: bool = False


class PCOSRiskResponse(BaseModel):
    risk_level: str
    score: int
    max_score: int
    recommendations: list[str]
    disclaimer: str = "Ce questionnaire est indicatif. Consultez un médecin pour un diagnostic."


class EndoResourcesResponse(BaseModel):
    description: str
    common_symptoms: list[str]
    diagnostic_tests: list[str]
    questions_for_doctor: list[str]
    disclaimer: str
