from __future__ import annotations

import enum
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PostCategory(str, enum.Enum):
    cycle = "cycle"
    fertility = "fertility"
    pregnancy = "pregnancy"
    hormonal_health = "hormonal_health"
    menopause = "menopause"
    nutrition = "nutrition"
    mental_health = "mental_health"
    intimate_health = "intimate_health"
    general = "general"


class CommunityPost(BaseModel):
    __tablename__ = "community_posts"
    __table_args__ = (Index("ix_community_posts_category", "category", "created_at"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    body_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[PostCategory] = mapped_column(Enum(PostCategory), nullable=False)
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    anonymous_display_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship()
