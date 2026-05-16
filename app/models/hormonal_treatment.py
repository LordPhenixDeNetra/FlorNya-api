from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class TreatmentType(str, enum.Enum):
    pill = "pill"
    patch = "patch"
    iud = "iud"
    implant = "implant"
    injection = "injection"
    ring = "ring"
    other = "other"


class HormonalTreatment(BaseModel):
    """User's hormonal treatment / contraception tracking."""

    __tablename__ = "hormonal_treatments"
    __table_args__ = (Index("ix_hormonal_treatments_user", "user_id"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    treatment_type: Mapped[TreatmentType] = mapped_column(Enum(TreatmentType), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reminder_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    side_effects_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
