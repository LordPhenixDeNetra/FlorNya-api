import uuid

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_chat_service, require_bloom
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.chat import ChatMessagePublic, ChatRequest, ChatResponse, ChatSessionPublic
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    data: ChatRequest,
    current_user: User = Depends(require_bloom),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.send_message(current_user, data)


@router.get("/sessions", response_model=list[ChatSessionPublic])
@limiter.limit("60/minute")
async def list_sessions(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: ChatService = Depends(get_chat_service),
) -> list[ChatSessionPublic]:
    return await service.list_sessions(current_user)


@router.get("/sessions/{session_id}", response_model=list[ChatMessagePublic])
@limiter.limit("60/minute")
async def get_session_history(
    request: Request,
    session_id: uuid.UUID,
    current_user: User = Depends(require_bloom),
    service: ChatService = Depends(get_chat_service),
) -> list[ChatMessagePublic]:
    return await service.get_session_history(current_user, session_id)
