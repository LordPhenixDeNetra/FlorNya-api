from __future__ import annotations

import enum
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Index, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CervicalMucusType(str, enum.Enum):
    dry = "dry"
    creamy = "creamy"
    watery = "watery"
    egg_white = "egg_white"


class LHTestResult(str, enum.Enum):
    negative = "negative"
    positive = "positive"
    peak = "peak"


class FertilityLog(BaseModel):
    """Daily fertility observation log — one row per user per day."""

    __tablename__ = "fertility_logs"
    __table_args__ = (
        CheckConstraint(
            "bbt_celsius IS NULL OR (bbt_celsius >= 35.0 AND bbt_celsius <= 40.0)",
            name="ck_fertility_logs_bbt",
        ),
        Index("ix_fertility_logs_user_date", "user_id", "log_date", unique=True),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    bbt_celsius: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    cervical_mucus: Mapped[CervicalMucusType | None] = mapped_column(Enum(CervicalMucusType), nullable=True)
    lh_test_result: Mapped[LHTestResult | None] = mapped_column(Enum(LHTestResult), nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
