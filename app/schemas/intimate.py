from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LibidoLogCreate(BaseModel):
    log_date: date
    score: int = Field(ge=1, le=5)
    notes: str | None = Field(default=None, max_length=2000)


class LibidoLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    score: int
    notes: str | None
    created_at: datetime


class IntimateHealthLogCreate(BaseModel):
    log_date: date
    vaginal_dryness_severity: int | None = Field(default=None, ge=1, le=5)
    discharge_type: str | None = None
    pain_during_intercourse: bool | None = None
    pain_intensity: int | None = Field(default=None, ge=1, le=10)
    itching: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)


class IntimateHealthLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    vaginal_dryness_severity: int | None
    discharge_type: str | None
    pain_during_intercourse: bool | None
    pain_intensity: int | None
    itching: bool | None
    notes: str | None
    created_at: datetime


class ContraceptionMethod(BaseModel):
    id: str
    name: str
    type: str
    effectiveness_pct: float
    description: str
    pros: list[str]
    cons: list[str]
    suitable_for: list[str]
    requires_prescription: bool


class VaginalHealthInfo(BaseModel):
    discharge_guide: list[dict]
    infection_signs: list[str]
    hygiene_tips: list[str]
    when_to_consult: list[str]


class SexualEducationContent(BaseModel):
    category: str
    title: str
    summary: str
    key_points: list[str]
    age_group: str
