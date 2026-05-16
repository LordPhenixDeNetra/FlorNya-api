from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MoodLog(BaseModel):
    __tablename__ = "mood_logs"
    __table_args__ = (
        CheckConstraint("mood_score >= 1 AND mood_score <= 5", name="ck_mood_logs_mood_score"),
        Index("ix_mood_logs_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    journal_text_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="mood_logs")
