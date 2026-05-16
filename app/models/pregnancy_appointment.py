from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AppointmentType(str, enum.Enum):
    prenatal_visit = "prenatal_visit"
    ultrasound = "ultrasound"
    blood_test = "blood_test"
    other = "other"


class PregnancyAppointment(BaseModel):
    __tablename__ = "pregnancy_appointments"
    __table_args__ = (Index("ix_preg_appointments_user_date", "user_id", "appointment_date"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType), default=AppointmentType.prenatal_visit, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    reminder_sent_7d: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_sent_1d: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
