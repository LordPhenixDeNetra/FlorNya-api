from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MentalAlertType(str, enum.Enum):
    distress = "distress"
    spm = "spm"
    tdpm = "tdpm"


class MentalAlert(BaseModel):
    __tablename__ = "mental_alerts"
    __table_args__ = (Index("ix_mental_alerts_user", "user_id", "created_at"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    alert_type: Mapped[MentalAlertType] = mapped_column(Enum(MentalAlertType), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resources_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship()
