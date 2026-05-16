from __future__ import annotations

import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_user_session", "user_id", "session_id", "created_at"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole), nullable=False)
    content_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship()
