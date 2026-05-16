import enum
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserPlan(str, enum.Enum):
    free = "free"
    essential = "essential"
    bloom = "bloom"
    bloom_pro = "bloom_pro"


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str | None
    photo_url: str | None
    date_of_birth: date
    language: str
    plan: UserPlan
    is_2fa_enabled: bool
    onboarding_completed: bool
    created_at: datetime


class UserUpdate(BaseModel):
    language: str | None = Field(default=None, min_length=2, max_length=8)
    first_name: str | None = Field(default=None, max_length=100)


class HealthCondition(str, enum.Enum):
    pcos = "pcos"
    endometriosis = "endometriosis"
    none = "none"


class ReproductiveStage(str, enum.Enum):
    menstruating = "menstruating"
    trying_to_conceive = "trying_to_conceive"
    pregnant = "pregnant"
    postpartum = "postpartum"
    perimenopause = "perimenopause"
    menopause = "menopause"


class OnboardingRequest(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    reproductive_stage: ReproductiveStage = ReproductiveStage.menstruating
    cycle_length: int = Field(default=28, ge=15, le=60)
    period_length: int = Field(default=5, ge=1, le=15)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    health_conditions: list[HealthCondition] = Field(default_factory=list)
    cuisine_preference: str | None = Field(default=None, max_length=100)


class ExtendedProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    photo_url: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None, min_length=2, max_length=8)
    allergies: list[str] = Field(default_factory=list)
    health_conditions: list[HealthCondition] = Field(default_factory=list)


class FemaleProfileUpsert(BaseModel):
    reproductive_stage: ReproductiveStage = ReproductiveStage.menstruating
    cycle_length: int = Field(default=28, ge=15, le=60)
    period_length: int = Field(default=5, ge=1, le=15)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)


class FemaleProfilePublic(FemaleProfileUpsert):
    id: UUID
    user_id: UUID
    created_at: datetime


class DevicePlatform(str, enum.Enum):
    ios = "ios"
    android = "android"
    web = "web"


class DeviceTokenRegister(BaseModel):
    token: str = Field(..., min_length=10, max_length=512)
    platform: DevicePlatform
