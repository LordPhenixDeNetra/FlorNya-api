from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage, ChatRole


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_message(
        self,
        user_id: UUID,
        session_id: UUID,
        role: ChatRole,
        content_encrypted: str,
        token_count: int | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content_encrypted=content_encrypted,
            token_count=token_count,
        )
        self.session.add(msg)
        return msg

    async def get_session_history(self, user_id: UUID, session_id: UUID, limit: int = 20) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id, ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_sessions(self, user_id: UUID) -> list[dict]:
        from sqlalchemy import func
        result = await self.session.execute(
            select(
                ChatMessage.session_id,
                func.count(ChatMessage.id).label("message_count"),
                func.max(ChatMessage.created_at).label("last_message_at"),
            )
            .where(ChatMessage.user_id == user_id)
            .group_by(ChatMessage.session_id)
            .order_by(func.max(ChatMessage.created_at).desc())
            .limit(10)
        )
        rows = result.all()
        return [{"session_id": r.session_id, "message_count": r.message_count, "last_message_at": r.last_message_at} for r in rows]
