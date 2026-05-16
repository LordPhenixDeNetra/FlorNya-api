import enum
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CervicalMucusType(str, enum.Enum):
    dry = "dry"
    creamy = "creamy"
    watery = "watery"
    egg_white = "egg_white"


class LHTestResult(str, enum.Enum):
    negative = "negative"
    positive = "positive"
    peak = "peak"


class FertilityLogCreate(BaseModel):
    log_date: date
    bbt_celsius: Decimal | None = Field(default=None, ge=35, le=40)
    cervical_mucus: CervicalMucusType | None = None
    lh_test_result: LHTestResult | None = None
    notes: str | None = Field(default=None, max_length=2000)


class FertilityLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    bbt_celsius: Decimal | None
    cervical_mucus: CervicalMucusType | None
    lh_test_result: LHTestResult | None
    notes: str | None
    created_at: datetime


class FertilityScoreResponse(BaseModel):
    date: date
    score: float = Field(ge=0, le=100)
    fertile: bool
    ovulation_predicted: bool
    details: str


class ConceptionAttemptCreate(BaseModel):
    attempt_date: date
    notes: str | None = Field(default=None, max_length=5000)


class ConceptionAttemptPublic(BaseModel):
    id: UUID
    user_id: UUID
    attempt_date: date
    notes: str | None
    created_at: datetime


class ConceptionModeToggle(BaseModel):
    active: bool


class FertilityCoachRequest(BaseModel):
    question: str = Field(max_length=1000)


class FertilityCoachResponse(BaseModel):
    answer: str
    disclaimer: str = "Ces informations sont données à titre indicatif et ne remplacent pas un avis médical."
