from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class JournalPromptType(str, enum.Enum):
    free = "free"
    gratitude = "gratitude"
    challenge = "challenge"
    reflection = "reflection"
    ai_generated = "ai_generated"


class EmotionalJournalEntry(BaseModel):
    __tablename__ = "emotional_journal_entries"
    __table_args__ = (
        Index("ix_emotional_journal_user_date", "user_id", "log_date"),
        CheckConstraint(
            "mood_score_at_entry IS NULL OR (mood_score_at_entry >= 1 AND mood_score_at_entry <= 5)",
            name="ck_emotional_journal_mood_score",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    prompt_type: Mapped[JournalPromptType] = mapped_column(
        Enum(JournalPromptType), default=JournalPromptType.free, nullable=False
    )
    prompt_text_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    mood_score_at_entry: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship()
