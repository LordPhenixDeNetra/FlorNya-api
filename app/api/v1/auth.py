from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_auth_service
from app.config import get_settings
from app.core.middleware import limiter
from app.core.security import decode_token
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

settings = get_settings()

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request, data: RegisterRequest, service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        access, refresh = await service.register(
            email=data.email,
            password=data.password,
            date_of_birth=data.date_of_birth,
            language=data.language,
        )
    except ValueError as exc:
        if str(exc) == "minimum_age_not_met":
            raise HTTPException(status_code=403, detail="minimum_age_not_met") from exc
        if str(exc) == "email_already_registered":
            raise HTTPException(status_code=409, detail="email_already_registered") from exc
        raise HTTPException(status_code=400, detail="invalid_request") from exc
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(request: Request, data: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    try:
        access, refresh = await service.login(email=data.email, password=data.password)
    except ValueError as exc:
        if str(exc) == "locked_out":
            raise HTTPException(status_code=429, detail="locked_out") from exc
        raise HTTPException(status_code=401, detail="invalid_credentials") from exc
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh(
    request: Request, data: RefreshRequest, service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("typ") != "refresh":
            raise ValueError("invalid_refresh")
        sub = payload.get("sub")
        jti = payload.get("jti")
        ver = payload.get("ver")
        if not isinstance(sub, str) or not isinstance(jti, str) or not isinstance(ver, int):
            raise ValueError("invalid_refresh")
        access, refresh_token = await service.refresh(user_id=UUID(sub), jti=jti, token_version=ver)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid_refresh") from exc
    return TokenResponse(access_token=access, refresh_token=refresh_token)
