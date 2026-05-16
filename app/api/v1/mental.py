from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user, get_mental_service
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.common import CursorPaginatedResponse
from app.schemas.mental import MoodFilterParams, MoodLogCreate, MoodLogPublic
from app.services.mental_service import MentalService

router = APIRouter()


@router.post("/mood", response_model=MoodLogPublic)
@limiter.limit("60/minute")
async def create_mood(
    request: Request,
    data: MoodLogCreate,
    current_user: User = Depends(get_current_user),
    service: MentalService = Depends(get_mental_service),
) -> MoodLogPublic:
    return await service.create_mood(current_user, data)


@router.get("/moods", response_model=CursorPaginatedResponse[MoodLogPublic])
@limiter.limit("60/minute")
async def list_moods(
    request: Request,
    params: MoodFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: MentalService = Depends(get_mental_service),
) -> CursorPaginatedResponse[MoodLogPublic]:
    return await service.list_moods(current_user, params)
