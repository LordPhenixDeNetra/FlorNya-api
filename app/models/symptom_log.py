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
        CheckConstraint(
            "sleep_quality IS NULL OR (sleep_quality >= 1 AND sleep_quality <= 5)",
            name="ck_symptom_logs_sleep_quality",
        ),
        CheckConstraint(
            "libido IS NULL OR (libido >= 1 AND libido <= 5)",
            name="ck_symptom_logs_libido",
        ),
        CheckConstraint(
            "intensity IS NULL OR (intensity >= 1 AND intensity <= 3)",
            name="ck_symptom_logs_intensity",
        ),
        Index("ix_symptom_logs_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Symptômes booléens
    cramps: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    bloating: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    breast_tenderness: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    headache: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    acne: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fatigue: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Symptômes graduels (1-5)
    energy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    libido: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Intensité générale (1-3)
    intensity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="symptom_logs")
