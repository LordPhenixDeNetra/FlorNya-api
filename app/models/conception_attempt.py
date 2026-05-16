from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ConceptionAttempt(BaseModel):
    """Private encrypted journal of conception attempts."""

    __tablename__ = "conception_attempts"
    __table_args__ = (Index("ix_conception_attempts_user_date", "user_id", "attempt_date"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    attempt_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
