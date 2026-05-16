from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class FlowIntensity(str, enum.Enum):
    spotting = "spotting"
    light = "light"
    medium = "medium"
    heavy = "heavy"


class CycleRecord(BaseModel):
    __tablename__ = "cycle_records"
    __table_args__ = (
        CheckConstraint("cycle_length >= 15 AND cycle_length <= 60", name="ck_cycle_records_cycle_length"),
        CheckConstraint(
            "period_end IS NULL OR period_end >= period_start",
            name="ck_cycle_records_period_end",
        ),
        Index("ix_cycle_records_user_date", "user_id", "period_start"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    cycle_length: Mapped[int] = mapped_column(Integer, default=28, nullable=False)
    flow_intensity: Mapped[FlowIntensity | None] = mapped_column(Enum(FlowIntensity), nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="cycle_records")
