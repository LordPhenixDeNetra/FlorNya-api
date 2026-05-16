from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PregnancyStatus(str, enum.Enum):
    active = "active"
    postpartum = "postpartum"
    ended = "ended"


class PregnancyProfile(BaseModel):
    """Active pregnancy or postpartum state for a user."""

    __tablename__ = "pregnancy_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_pregnancy_profiles_user"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[PregnancyStatus] = mapped_column(
        Enum(PregnancyStatus), default=PregnancyStatus.active, nullable=False
    )
    lmp_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_breastfeeding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weeks_at_activation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
