from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LibidoLog(BaseModel):
    __tablename__ = "libido_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_libido_logs_user_date"),
        CheckConstraint(
            "score >= 1 AND score <= 5",
            name="ck_libido_logs_score",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()


Index("ix_libido_logs_user_date", LibidoLog.user_id, LibidoLog.log_date)
