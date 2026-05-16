import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReminderType(str, enum.Enum):
    period = "period"
    medication = "medication"
    hydration = "hydration"
    mood_checkin = "mood_checkin"


class ReminderConfigCreate(BaseModel):
    is_enabled: bool = True
    time_of_day: str = Field(default="20:00", pattern=r"^\d{2}:\d{2}$")
    label: str | None = Field(default=None, max_length=200)


class ReminderConfigPublic(BaseModel):
    id: UUID
    user_id: UUID
    reminder_type: ReminderType
    is_enabled: bool
    time_of_day: str
    label: str | None
    created_at: datetime
