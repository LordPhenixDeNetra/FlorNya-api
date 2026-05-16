import enum
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PregnancyStatus(str, enum.Enum):
    active = "active"
    postpartum = "postpartum"
    ended = "ended"


class AppointmentType(str, enum.Enum):
    prenatal_visit = "prenatal_visit"
    ultrasound = "ultrasound"
    blood_test = "blood_test"
    other = "other"


class BreastSide(str, enum.Enum):
    left = "left"
    right = "right"
    both = "both"


class PregnancyActivate(BaseModel):
    lmp_date: date | None = None
    due_date: date | None = None
    weeks_at_activation: int | None = Field(default=None, ge=1, le=42)


class PregnancyProfilePublic(BaseModel):
    id: UUID
    user_id: UUID
    status: PregnancyStatus
    lmp_date: date | None
    due_date: date | None
    delivery_date: date | None
    is_breastfeeding: bool
    current_week: int | None
    created_at: datetime


class PregnancyWeekInfo(BaseModel):
    week: int
    trimester: int
    baby_size_comparison: str
    baby_length_cm: float | None
    baby_weight_g: int | None
    key_development: str
    tips_for_mother: str


class PregnancySymptomCreate(BaseModel):
    log_date: date
    nausea: bool | None = None
    vomiting: bool | None = None
    fatigue: bool | None = None
    back_pain: bool | None = None
    swelling: bool | None = None
    heartburn: bool | None = None
    headache: bool | None = None
    fetal_movement_count: int | None = Field(default=None, ge=0)
    severity: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=5000)


class PregnancySymptomPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    nausea: bool | None
    vomiting: bool | None
    fatigue: bool | None
    back_pain: bool | None
    swelling: bool | None
    heartburn: bool | None
    headache: bool | None
    fetal_movement_count: int | None
    severity: int | None
    is_alarm_symptom: bool
    notes: str | None
    created_at: datetime


class AppointmentCreate(BaseModel):
    appointment_date: date
    appointment_type: AppointmentType = AppointmentType.prenatal_visit
    title: str = Field(max_length=200)
    location: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=5000)


class AppointmentPublic(BaseModel):
    id: UUID
    user_id: UUID
    appointment_date: date
    appointment_type: AppointmentType
    title: str
    location: str | None
    notes: str | None
    created_at: datetime


class BreastfeedingSessionCreate(BaseModel):
    session_date: date
    started_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    breast_side: BreastSide | None = None
    quantity_ml: int | None = Field(default=None, ge=0)


class BreastfeedingSessionPublic(BaseModel):
    id: UUID
    user_id: UUID
    session_date: date
    started_at: datetime | None
    duration_minutes: int | None
    breast_side: BreastSide | None
    quantity_ml: int | None
    created_at: datetime


class EPDSCreate(BaseModel):
    answers: list[int] = Field(min_length=10, max_length=10)

    @property
    def total_score(self) -> int:
        return sum(self.answers)


class EPDSPublic(BaseModel):
    id: UUID
    user_id: UUID
    assessment_date: date
    total_score: int
    alert_level: str
    message: str
    created_at: datetime


class PostpartumActivate(BaseModel):
    delivery_date: date
