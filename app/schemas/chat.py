from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: UUID | None = None


class ChatMessagePublic(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: UUID
    message: ChatMessagePublic
    reply: ChatMessagePublic


class ChatSessionPublic(BaseModel):
    session_id: UUID
    message_count: int
    last_message_at: datetime
    preview: str
