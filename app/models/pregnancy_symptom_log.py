from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PregnancySymptomLog(BaseModel):
    """Daily symptom tracking during pregnancy."""

    __tablename__ = "pregnancy_symptom_logs"
    __table_args__ = (
        CheckConstraint(
            "fetal_movement_count IS NULL OR fetal_movement_count >= 0",
            name="ck_preg_sym_fetal_movement",
        ),
        CheckConstraint(
            "severity IS NULL OR (severity >= 1 AND severity <= 5)",
            name="ck_preg_sym_severity",
        ),
        Index("ix_pregnancy_symptom_logs_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)

    nausea: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    vomiting: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fatigue: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    back_pain: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    swelling: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    heartburn: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    headache: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fetal_movement_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_alarm_symptom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
