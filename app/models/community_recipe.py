from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CommunityRecipe(BaseModel):
    __tablename__ = "community_recipes"
    __table_args__ = (
        Index("ix_community_recipes_phase", "phase", "created_at"),
        CheckConstraint(
            "nutrition_score IS NULL OR (nutrition_score >= 1 AND nutrition_score <= 10)",
            name="ck_community_recipes_score",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingredients_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cultural_cuisine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nutrition_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_approved: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped["User"] = relationship()
