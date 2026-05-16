from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import ARRAY, Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PainLog(BaseModel):
    """Pelvic pain journal for endometriosis / PCOS tracking."""

    __tablename__ = "pain_logs"
    __table_args__ = (
        CheckConstraint(
            "pain_intensity IS NULL OR (pain_intensity >= 1 AND pain_intensity <= 10)",
            name="ck_pain_logs_intensity",
        ),
        Index("ix_pain_logs_user_date", "user_id", "log_date"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    pain_intensity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pelvic: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    lower_back: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dysmenorrhea: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dyspareunia: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    bloating: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    body_zones: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
