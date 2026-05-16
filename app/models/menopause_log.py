from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MenopauseLog(BaseModel):
    """Daily menopause / perimenopause symptom log."""

    __tablename__ = "menopause_logs"
    __table_args__ = (
        CheckConstraint(
            "severity IS NULL OR (severity >= 1 AND severity <= 5)",
            name="ck_menopause_logs_severity",
        ),
        Index("ix_menopause_logs_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)

    hot_flash_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    night_sweats: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    vaginal_dryness: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    insomnia: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    mood_swings: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    weight_gain: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    brain_fog: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    joint_pain: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
