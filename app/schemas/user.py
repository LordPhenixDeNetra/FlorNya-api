import enum
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserPlan(str, enum.Enum):
    free = "free"
    bloom = "bloom"
    bloom_pro = "bloom_pro"


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    date_of_birth: date
    language: str
    plan: UserPlan
    created_at: datetime


class UserUpdate(BaseModel):
    language: str | None = Field(default=None, min_length=2, max_length=8)


class ReproductiveStage(str, enum.Enum):
    menstruating = "menstruating"
    trying_to_conceive = "trying_to_conceive"
    pregnant = "pregnant"
    postpartum = "postpartum"
    perimenopause = "perimenopause"
    menopause = "menopause"


class FemaleProfileUpsert(BaseModel):
    reproductive_stage: ReproductiveStage = ReproductiveStage.menstruating
    cycle_length: int = Field(default=28, ge=15, le=60)
    period_length: int = Field(default=5, ge=1, le=15)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)


class FemaleProfilePublic(FemaleProfileUpsert):
    id: UUID
    user_id: UUID
    created_at: datetime
