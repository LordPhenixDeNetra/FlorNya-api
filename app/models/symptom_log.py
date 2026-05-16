from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SymptomLog(BaseModel):
    __tablename__ = "symptom_logs"
    __table_args__ = (
        CheckConstraint("energy IS NULL OR (energy >= 1 AND energy <= 5)", name="ck_symptom_logs_energy"),
        Index("ix_symptom_logs_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    cramps: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    energy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="symptom_logs")
