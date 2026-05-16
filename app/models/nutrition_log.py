from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class NutritionLog(BaseModel):
    """Daily food journal with AI-estimated hormonal impact."""

    __tablename__ = "nutrition_logs"
    __table_args__ = (
        CheckConstraint(
            "hormonal_impact_score IS NULL OR (hormonal_impact_score >= 1 AND hormonal_impact_score <= 10)",
            name="ck_nutrition_logs_impact",
        ),
        Index("ix_nutrition_logs_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    meals_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    hormonal_impact_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_analysis_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    water_glasses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
