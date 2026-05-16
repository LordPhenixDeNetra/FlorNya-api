from __future__ import annotations

import enum
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserPlan(str, enum.Enum):
    free = "free"
    essential = "essential"
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

    # Profil étendu
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 2FA
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reset password
    password_reset_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Stripe
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Phase 3
    beta_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    female_profile: Mapped[FemaleProfile | None] = relationship(back_populates="user", uselist=False)
    cycle_records: Mapped[list[CycleRecord]] = relationship(back_populates="user")
    symptom_logs: Mapped[list[SymptomLog]] = relationship(back_populates="user")
    mood_logs: Mapped[list[MoodLog]] = relationship(back_populates="user")
    reminders: Mapped[list[ReminderConfig]] = relationship(back_populates="user")


Index("ix_users_active", User.is_active, User.deleted_at)
