from __future__ import annotations

import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ReproductiveStage(str, enum.Enum):
    menstruating = "menstruating"
    trying_to_conceive = "trying_to_conceive"
    pregnant = "pregnant"
    postpartum = "postpartum"
    perimenopause = "perimenopause"
    menopause = "menopause"


class FemaleProfile(BaseModel):
    __tablename__ = "female_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_female_profiles_user_id"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reproductive_stage: Mapped[ReproductiveStage] = mapped_column(
        Enum(ReproductiveStage), default=ReproductiveStage.menstruating, nullable=False
    )
    cycle_length: Mapped[int] = mapped_column(Integer, default=28, nullable=False)
    period_length: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)

    user: Mapped["User"] = relationship(back_populates="female_profile")
