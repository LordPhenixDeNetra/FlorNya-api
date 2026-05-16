from __future__ import annotations

import enum
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ReminderType(str, enum.Enum):
    period = "period"
    medication = "medication"
    hydration = "hydration"
    mood_checkin = "mood_checkin"


class ReminderConfig(BaseModel):
    __tablename__ = "reminder_configs"
    __table_args__ = (Index("ix_reminder_configs_user_type", "user_id", "reminder_type"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reminder_type: Mapped[ReminderType] = mapped_column(Enum(ReminderType), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    time_of_day: Mapped[str] = mapped_column(String(5), default="20:00", nullable=False)
    label_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="reminders")
