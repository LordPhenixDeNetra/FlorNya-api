from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user, get_user_service
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.user import FemaleProfilePublic, FemaleProfileUpsert, UserPublic, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserPublic)
@limiter.limit("60/minute")
async def me(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserPublic:
    return await service.get_me(current_user)


@router.put("/me", response_model=UserPublic)
@limiter.limit("30/minute")
async def update_me(
    request: Request,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserPublic:
    return await service.update_me(current_user, data)


@router.get("/me/female-profile", response_model=FemaleProfilePublic)
@limiter.limit("60/minute")
async def get_female_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> FemaleProfilePublic:
    profile = await service.get_female_profile(current_user)
    if profile is None:
        raise HTTPException(status_code=404, detail="female_profile_not_found")
    return profile


@router.put("/me/female-profile", response_model=FemaleProfilePublic)
@limiter.limit("30/minute")
async def upsert_female_profile(
    request: Request,
    data: FemaleProfileUpsert,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> FemaleProfilePublic:
    return await service.upsert_female_profile(current_user, data)
