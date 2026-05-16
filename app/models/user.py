from __future__ import annotations

import enum
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserPlan(str, enum.Enum):
    free = "free"
    bloom = "bloom"
    bloom_pro = "bloom_pro"


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    language: Mapped[str] = mapped_column(String(8), default="fr", nullable=False)
    plan: Mapped[UserPlan] = mapped_column(Enum(UserPlan), default=UserPlan.free, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    token_version: Mapped[int] = mapped_column(default=0, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    female_profile: Mapped[FemaleProfile | None] = relationship(back_populates="user", uselist=False)
    cycle_records: Mapped[list[CycleRecord]] = relationship(back_populates="user")
    symptom_logs: Mapped[list[SymptomLog]] = relationship(back_populates="user")
    mood_logs: Mapped[list[MoodLog]] = relationship(back_populates="user")


Index("ix_users_active", User.is_active, User.deleted_at)
