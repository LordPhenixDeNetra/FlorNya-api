from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, Enum, ForeignKey, Index, Integer, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DischargeType(str, enum.Enum):
    none = "none"
    normal_clear = "normal_clear"
    normal_white = "normal_white"
    abnormal_yellow = "abnormal_yellow"
    abnormal_green = "abnormal_green"
    abnormal_gray = "abnormal_gray"
    other = "other"


class IntimateHealthLog(BaseModel):
    __tablename__ = "intimate_health_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_intimate_health_logs_user_date"),
        CheckConstraint(
            "vaginal_dryness_severity IS NULL OR (vaginal_dryness_severity >= 1 AND vaginal_dryness_severity <= 5)",
            name="ck_intimate_health_dryness",
        ),
        CheckConstraint(
            "pain_intensity IS NULL OR (pain_intensity >= 1 AND pain_intensity <= 10)",
            name="ck_intimate_health_pain",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    vaginal_dryness_severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discharge_type: Mapped[DischargeType | None] = mapped_column(Enum(DischargeType), nullable=True)
    pain_during_intercourse: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    pain_intensity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    itching: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()


Index("ix_intimate_health_logs_user_date", IntimateHealthLog.user_id, IntimateHealthLog.log_date)
