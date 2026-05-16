from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConsultationBookingCreate(BaseModel):
    scheduled_at: datetime
    practitioner_name: str | None = Field(default=None, max_length=200)


class ConsultationBookingPublic(BaseModel):
    id: UUID
    user_id: UUID
    scheduled_at: datetime
    status: str
    practitioner_name: str | None
    preparation_notes: str | None
    video_url: str | None
    summary: str | None
    created_at: datetime


class ConsultationPrepResponse(BaseModel):
    generated_at: datetime
    cycle_summary: str
    recent_symptoms: list[str]
    mood_summary: str
    suggested_questions: list[str]
    key_concerns: list[str]
    full_prep_notes: str


class MonthlyReportRequest(BaseModel):
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)
