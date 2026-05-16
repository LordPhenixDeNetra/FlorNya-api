from __future__ import annotations

import enum
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BreastSide(str, enum.Enum):
    left = "left"
    right = "right"
    both = "both"


class BreastfeedingSession(BaseModel):
    __tablename__ = "breastfeeding_sessions"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="ck_breastfeeding_duration",
        ),
        Index("ix_breastfeeding_sessions_user_date", "user_id", "session_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    breast_side: Mapped[BreastSide | None] = mapped_column(Enum(BreastSide), nullable=True)
    quantity_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship()
