from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import (
    get_current_user,
    get_device_token_repository,
    get_user_service,
)
from app.core.middleware import limiter
from app.models.user import User
from app.repositories.device_token_repository import DeviceTokenRepository
from app.schemas.user import (
    DeviceTokenRegister,
    ExtendedProfileUpdate,
    FemaleProfilePublic,
    FemaleProfileUpsert,
    OnboardingRequest,
    UserPublic,
    UserUpdate,
)
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


@router.patch("/me/extended-profile", response_model=UserPublic)
@limiter.limit("30/minute")
async def update_extended_profile(
    request: Request,
    data: ExtendedProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserPublic:
    return await service.update_extended_profile(current_user, data)


@router.post("/me/onboarding", response_model=UserPublic)
@limiter.limit("10/minute")
async def complete_onboarding(
    request: Request,
    data: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserPublic:
    return await service.complete_onboarding(current_user, data)


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


@router.get("/me/export")
@limiter.limit("3/day")
async def export_data(
    request: Request,
    format: str = "json",
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> StreamingResponse:
    if format not in ("json", "csv"):
        raise HTTPException(status_code=400, detail="invalid_format")
    data = await service.export_data(current_user, format)
    media_type = "application/json" if format == "json" else "text/csv"
    filename = f"flornya_export_{current_user.id}.{format}"
    return StreamingResponse(
        iter([data]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/me", status_code=204)
@limiter.limit("3/day")
async def delete_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> Response:
    await service.delete_account(current_user)
    return Response(status_code=204)


@router.post("/me/device-token", status_code=201)
@limiter.limit("20/minute")
async def register_device_token(
    request: Request,
    data: DeviceTokenRegister,
    current_user: User = Depends(get_current_user),
    device_repo: DeviceTokenRepository = Depends(get_device_token_repository),
) -> dict:
    dt = await device_repo.upsert(current_user.id, data.token, data.platform)
    await device_repo.session.commit()
    return {"id": str(dt.id), "platform": dt.platform, "is_active": dt.is_active}


@router.delete("/me/device-token", status_code=204)
@limiter.limit("20/minute")
async def unregister_device_token(
    request: Request,
    data: DeviceTokenRegister,
    current_user: User = Depends(get_current_user),
    device_repo: DeviceTokenRepository = Depends(get_device_token_repository),
) -> Response:
    await device_repo.deactivate(current_user.id, data.token)
    await device_repo.session.commit()
    return Response(status_code=204)


@router.post("/me/avatar", response_model=UserPublic)
@limiter.limit("10/day")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserPublic:
    from app.config import get_settings

    settings = get_settings()
    max_bytes = settings.AVATAR_MAX_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="avatar_too_large")
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=415, detail="unsupported_image_format")
    return await service.upload_avatar(current_user, content, file.content_type)


@router.post("/me/beta-activate", response_model=UserPublic)
@limiter.limit("5/minute")
async def activate_beta(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserPublic:
    return await service.activate_beta(current_user)
