from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import get_auth_service, get_current_user
from app.config import get_settings
from app.core.middleware import limiter
from app.core.security import decode_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    TotpDisableRequest,
    TotpSetupResponse,
    TotpVerifyRequest,
    TwoFactorLoginVerify,
    TwoFactorRequired,
)
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


@router.post("/login")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request, data: LoginRequest, service: AuthService = Depends(get_auth_service)
) -> TokenResponse | TwoFactorRequired:
    try:
        result = await service.login(email=data.email, password=data.password)
    except ValueError as exc:
        if str(exc) == "locked_out":
            raise HTTPException(status_code=429, detail="locked_out") from exc
        raise HTTPException(status_code=401, detail="invalid_credentials") from exc

    if isinstance(result, dict):
        return TwoFactorRequired(**result)
    access, refresh = result
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


# ── Password reset ──────────────────────────────────────────────────────


@router.post("/password-reset/request", status_code=204)
@limiter.limit(settings.RATE_LIMIT_PASSWORD_RESET)
async def password_reset_request(
    request: Request, data: PasswordResetRequest, service: AuthService = Depends(get_auth_service)
) -> Response:
    await service.request_password_reset(email=data.email)
    return Response(status_code=204)


@router.post("/password-reset/confirm", status_code=204)
@limiter.limit("10/minute")
async def password_reset_confirm(
    request: Request, data: PasswordResetConfirm, service: AuthService = Depends(get_auth_service)
) -> Response:
    try:
        await service.confirm_password_reset(token=data.token, new_password=data.new_password)
    except ValueError as exc:
        detail = str(exc) if str(exc) in ("invalid_reset_token", "reset_token_expired") else "invalid_request"
        raise HTTPException(status_code=400, detail=detail) from exc
    return Response(status_code=204)


# ── 2FA TOTP ─────────────────────────────────────────────────────────────


@router.post("/2fa/setup", response_model=TotpSetupResponse)
@limiter.limit("10/minute")
async def totp_setup(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> TotpSetupResponse:
    result = await service.setup_totp(user_id=current_user.id)
    return TotpSetupResponse(**result)


@router.post("/2fa/confirm", status_code=204)
@limiter.limit("10/minute")
async def totp_confirm(
    request: Request,
    data: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    try:
        await service.confirm_totp(user_id=current_user.id, code=data.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(status_code=204)


@router.post("/2fa/verify", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def totp_verify_login(
    request: Request,
    data: TwoFactorLoginVerify,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access, refresh = await service.verify_totp_login(
            challenge_token=data.challenge_token, code=data.code
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.delete("/2fa", status_code=204)
@limiter.limit("10/minute")
async def totp_disable(
    request: Request,
    data: TotpDisableRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    try:
        await service.disable_totp(user_id=current_user.id, code=data.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(status_code=204)


@router.post("/logout", status_code=204)
@limiter.limit("30/minute")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    """Révoque le JTI de l'access token courant et tous les refresh tokens."""
    auth = request.headers.get("authorization", "")
    access_token = auth.split(" ", 1)[1].strip() if " " in auth else ""
    await service.logout(access_token=access_token)
    await service._revoke_all_refresh_tokens(current_user.id)
    return Response(status_code=204)
