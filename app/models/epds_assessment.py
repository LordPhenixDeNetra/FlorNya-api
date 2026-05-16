from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

EPDS_ALERT_THRESHOLD = 13
EPDS_MODERATE_THRESHOLD = 10


class EPDSAssessment(BaseModel):
    """Edinburgh Postnatal Depression Scale assessment (sent every 15 days postpartum)."""

    __tablename__ = "epds_assessments"
    __table_args__ = (
        CheckConstraint(
            "total_score >= 0 AND total_score <= 30",
            name="ck_epds_score_range",
        ),
        Index("ix_epds_assessments_user_date", "user_id", "assessment_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    answers_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_sent: Mapped[bool] = mapped_column(
        __import__("sqlalchemy").Boolean, default=False, nullable=False
    )

    user: Mapped["User"] = relationship()
