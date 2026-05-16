from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CycleRecord(BaseModel):
    __tablename__ = "cycle_records"
    __table_args__ = (
        CheckConstraint("cycle_length >= 15 AND cycle_length <= 60", name="ck_cycle_records_cycle_length"),
        Index("ix_cycle_records_user_date", "user_id", "period_start"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    cycle_length: Mapped[int] = mapped_column(Integer, default=28, nullable=False)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="cycle_records")
