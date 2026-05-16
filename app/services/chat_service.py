import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.chat_message import ChatMessage, ChatRole
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatMessagePublic, ChatRequest, ChatResponse, ChatSessionPublic
from app.services.ai.anthropic_service import AnthropicInsightService


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        chat_repo: ChatRepository,
        ai_service: AnthropicInsightService | None = None,
    ):
        self.session = session
        self.chat_repo = chat_repo
        self.ai_service = ai_service

    async def send_message(self, user: User, data: ChatRequest) -> ChatResponse:
        session_id = data.session_id or uuid.uuid4()

        history = await self.chat_repo.get_session_history(user.id, session_id, limit=12)
        history_plain = [
            {"role": msg.role.value, "content": decrypt_sensitive(msg.content_encrypted) or ""}
            for msg in history
        ]

        context = await self._build_user_context(user)

        ai_reply = "Service IA non disponible. Consultez un professionnel de santé féminine."
        if self.ai_service:
            ai_reply = await self.ai_service.chat_response(data.message, history_plain, context)

        user_msg = await self.chat_repo.add_message(
            user_id=user.id,
            session_id=session_id,
            role=ChatRole.user,
            content_encrypted=encrypt_sensitive(data.message),
        )
        assistant_msg = await self.chat_repo.add_message(
            user_id=user.id,
            session_id=session_id,
            role=ChatRole.assistant,
            content_encrypted=encrypt_sensitive(ai_reply),
        )
        await self.session.commit()
        await self.session.refresh(user_msg)
        await self.session.refresh(assistant_msg)

        return ChatResponse(
            session_id=session_id,
            message=self._msg_to_public(user_msg),
            reply=self._msg_to_public(assistant_msg),
        )

    async def list_sessions(self, user: User) -> list[ChatSessionPublic]:
        sessions_raw = await self.chat_repo.list_sessions(user.id)
        result = []
        for s in sessions_raw:
            last_msgs = await self.chat_repo.get_session_history(user.id, s["session_id"], limit=1)
            preview = ""
            if last_msgs:
                raw = decrypt_sensitive(last_msgs[-1].content_encrypted) or ""
                preview = raw[:80] + "…" if len(raw) > 80 else raw
            result.append(ChatSessionPublic(
                session_id=s["session_id"],
                message_count=s["message_count"],
                last_message_at=s["last_message_at"],
                preview=preview,
            ))
        return result

    async def get_session_history(self, user: User, session_id: uuid.UUID) -> list[ChatMessagePublic]:
        messages = await self.chat_repo.get_session_history(user.id, session_id, limit=50)
        return [self._msg_to_public(m) for m in messages]

    async def _build_user_context(self, user: User) -> dict:
        from app.models.cycle_record import CycleRecord
        from app.models.female_profile import FemaleProfile

        context: dict = {
            "language": user.language,
            "first_name": user.first_name,
        }

        if user.date_of_birth:
            today = date.today()
            age = today.year - user.date_of_birth.year - (
                (today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day)
            )
            context["age"] = age

        profile_result = await self.session.execute(
            select(FemaleProfile).where(FemaleProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            context["reproductive_stage"] = profile.reproductive_stage
            context["cuisine_preference"] = profile.cuisine_preference

        cycle_result = await self.session.execute(
            select(CycleRecord).where(CycleRecord.user_id == user.id).order_by(CycleRecord.period_start.desc()).limit(1)
        )
        latest_cycle = cycle_result.scalar_one_or_none()
        if latest_cycle:
            cycle_day = (date.today() - latest_cycle.period_start).days + 1
            cycle_len = latest_cycle.cycle_length or 28
            if cycle_day <= 5:
                context["cycle_phase"] = "menstrual"
            elif cycle_day <= 13:
                context["cycle_phase"] = "follicular"
            elif cycle_day <= 16:
                context["cycle_phase"] = "ovulatory"
            else:
                context["cycle_phase"] = "luteal"

        return context

    def _msg_to_public(self, msg: ChatMessage) -> ChatMessagePublic:
        return ChatMessagePublic(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role.value,
            content=decrypt_sensitive(msg.content_encrypted) or "",
            created_at=msg.created_at,
        )
