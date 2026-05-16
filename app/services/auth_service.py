import base64
import io
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pyotp
import qrcode
import qrcode.image.svg
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.redis import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_sensitive,
    encrypt_sensitive,
    hash_password,
    verify_minimum_age,
    verify_password,
)
from app.interfaces.email_interface import IEmailService
from app.models.user import User
from app.repositories.user_repository import UserRepository

settings = get_settings()

_2FA_CHALLENGE_EXPIRE_MINUTES = 5


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        email_service: IEmailService | None = None,
    ):
        self.session = session
        self.users = users
        self.email_service = email_service

    # ── Register ─────────────────────────────────────────────────────────

    async def register(self, *, email: str, password: str, date_of_birth, language: str) -> tuple[str, str]:
        verify_minimum_age(date_of_birth)
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise ValueError("email_already_registered")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            date_of_birth=date_of_birth,
            language=language,
        )
        await self.users.add(user)
        await self.session.commit()

        if self.email_service:
            await self.email_service.send_welcome(to_email=email, first_name=None)

        access = create_access_token(user.id, user.token_version)
        refresh, jti = create_refresh_token(user.id, user.token_version)
        await self._store_refresh_jti(user.id, jti)
        return access, refresh

    # ── Login ─────────────────────────────────────────────────────────────

    async def login(self, *, email: str, password: str) -> tuple[str, str] | dict:
        await self._ensure_not_locked(email)
        user = await self.users.get_by_email(email)
        if user is None or user.deleted_at is not None or not user.is_active:
            await self._record_failed_login(email)
            raise ValueError("invalid_credentials")
        if not verify_password(password, user.hashed_password):
            await self._record_failed_login(email)
            raise ValueError("invalid_credentials")

        await self._clear_failed_login(email)

        if user.is_2fa_enabled:
            challenge = self._create_2fa_challenge(user.id, user.token_version)
            return {"requires_2fa": True, "challenge_token": challenge}

        access = create_access_token(user.id, user.token_version)
        refresh, jti = create_refresh_token(user.id, user.token_version)
        await self._store_refresh_jti(user.id, jti)
        return access, refresh

    # ── Refresh ───────────────────────────────────────────────────────────

    async def refresh(self, *, user_id: UUID, jti: str, token_version: int) -> tuple[str, str]:
        user = await self.users.get_active(user_id)
        if user is None:
            raise ValueError("invalid_refresh")
        if user.token_version != token_version:
            raise ValueError("invalid_refresh")

        key = f"refresh:{user_id}:{jti}"
        exists = await redis_client.exists(key)
        if not exists:
            raise ValueError("invalid_refresh")

        access = create_access_token(user.id, user.token_version)
        refresh, new_jti = create_refresh_token(user.id, user.token_version)
        await redis_client.delete(key)
        await self._store_refresh_jti(user.id, new_jti)
        return access, refresh

    # ── Password reset ────────────────────────────────────────────────────

    async def request_password_reset(self, *, email: str) -> None:
        user = await self.users.get_by_email(email)
        if user is None or user.deleted_at is not None:
            return  # Silent — security

        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )
        await self.session.commit()

        if self.email_service:
            await self.email_service.send_password_reset(
                to_email=user.email,
                token=token,
                first_name=user.first_name,
            )

    async def confirm_password_reset(self, *, token: str, new_password: str) -> None:
        user = await self.users.get_by_reset_token(token)
        if user is None:
            raise ValueError("invalid_reset_token")
        if user.password_reset_expires is None:
            raise ValueError("invalid_reset_token")

        expires = user.password_reset_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise ValueError("reset_token_expired")

        user.hashed_password = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.token_version += 1
        await self.session.commit()

        # Revoke all refresh tokens
        await self._revoke_all_refresh_tokens(user.id)

    # ── 2FA TOTP ──────────────────────────────────────────────────────────

    async def setup_totp(self, *, user_id: UUID) -> dict:
        user = await self.users.get_active(user_id)
        if user is None:
            raise ValueError("user_not_found")

        secret = pyotp.random_base32()
        user.totp_secret_encrypted = encrypt_sensitive(secret)
        await self.session.commit()

        otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=settings.TOTP_ISSUER,
        )

        img = qrcode.make(otpauth_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

        return {"secret": secret, "otpauth_url": otpauth_url, "qr_code_base64": qr_b64}

    async def confirm_totp(self, *, user_id: UUID, code: str) -> None:
        user = await self.users.get_active(user_id)
        if user is None or user.totp_secret_encrypted is None:
            raise ValueError("totp_not_setup")

        secret = decrypt_sensitive(user.totp_secret_encrypted)
        if secret is None or not pyotp.TOTP(secret).verify(code, valid_window=1):
            raise ValueError("invalid_totp_code")

        user.is_2fa_enabled = True
        await self.session.commit()

    async def verify_totp_login(self, *, challenge_token: str, code: str) -> tuple[str, str]:
        try:
            payload = decode_token(challenge_token)
        except ValueError as exc:
            raise ValueError("invalid_challenge_token") from exc

        if payload.get("typ") != "2fa_pending":
            raise ValueError("invalid_challenge_token")

        sub = payload.get("sub")
        ver = payload.get("ver")
        if not isinstance(sub, str) or not isinstance(ver, int):
            raise ValueError("invalid_challenge_token")

        user = await self.users.get_active(UUID(sub))
        if user is None or user.token_version != ver:
            raise ValueError("invalid_challenge_token")
        if not user.is_2fa_enabled or user.totp_secret_encrypted is None:
            raise ValueError("2fa_not_enabled")

        secret = decrypt_sensitive(user.totp_secret_encrypted)
        if secret is None or not pyotp.TOTP(secret).verify(code, valid_window=1):
            raise ValueError("invalid_totp_code")

        access = create_access_token(user.id, user.token_version)
        refresh, jti = create_refresh_token(user.id, user.token_version)
        await self._store_refresh_jti(user.id, jti)
        return access, refresh

    async def disable_totp(self, *, user_id: UUID, code: str) -> None:
        user = await self.users.get_active(user_id)
        if user is None or not user.is_2fa_enabled or user.totp_secret_encrypted is None:
            raise ValueError("2fa_not_enabled")

        secret = decrypt_sensitive(user.totp_secret_encrypted)
        if secret is None or not pyotp.TOTP(secret).verify(code, valid_window=1):
            raise ValueError("invalid_totp_code")

        user.is_2fa_enabled = False
        user.totp_secret_encrypted = None
        await self.session.commit()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _create_2fa_challenge(self, user_id: UUID, token_version: int) -> str:
        from datetime import timedelta
        from app.core.security import create_access_token
        from jose import jwt

        expire = datetime.now(timezone.utc) + timedelta(minutes=_2FA_CHALLENGE_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "typ": "2fa_pending",
            "exp": expire,
            "ver": token_version,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    async def _store_refresh_jti(self, user_id: UUID, jti: str) -> None:
        key = f"refresh:{user_id}:{jti}"
        ttl_seconds = 60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS
        await redis_client.set(key, "1", ex=ttl_seconds)

    async def _revoke_all_refresh_tokens(self, user_id: UUID) -> None:
        pattern = f"refresh:{user_id}:*"
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break

    async def _ensure_not_locked(self, email: str) -> None:
        key = f"login_fail:{email}"
        attempts_s = await redis_client.get(key)
        if attempts_s is None:
            return
        try:
            attempts = int(attempts_s)
        except ValueError:
            return
        if attempts >= settings.AUTH_LOCKOUT_MAX_ATTEMPTS:
            raise ValueError("locked_out")

    async def _record_failed_login(self, email: str) -> None:
        key = f"login_fail:{email}"
        attempts = await redis_client.incr(key)
        if attempts == 1:
            await redis_client.expire(key, settings.AUTH_LOCKOUT_SECONDS)

    async def _clear_failed_login(self, email: str) -> None:
        await redis_client.delete(f"login_fail:{email}")
