from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ConsultationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class ConsultationBooking(BaseModel):
    __tablename__ = "consultation_bookings"
    __table_args__ = (Index("ix_consultation_bookings_user", "user_id", "scheduled_at"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus), default=ConsultationStatus.pending, nullable=False
    )
    video_url_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    preparation_notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    practitioner_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
