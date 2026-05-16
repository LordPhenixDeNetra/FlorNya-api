from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_minimum_age,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.config import get_settings

settings = get_settings()


class AuthService:
    def __init__(self, session: AsyncSession, users: UserRepository):
        self.session = session
        self.users = users

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

        access = create_access_token(user.id, user.token_version)
        refresh, jti = create_refresh_token(user.id, user.token_version)
        await self._store_refresh_jti(user.id, jti)
        return access, refresh

    async def login(self, *, email: str, password: str) -> tuple[str, str]:
        await self._ensure_not_locked(email)
        user = await self.users.get_by_email(email)
        if user is None or user.deleted_at is not None or not user.is_active:
            await self._record_failed_login(email)
            raise ValueError("invalid_credentials")
        if not verify_password(password, user.hashed_password):
            await self._record_failed_login(email)
            raise ValueError("invalid_credentials")

        await self._clear_failed_login(email)
        access = create_access_token(user.id, user.token_version)
        refresh, jti = create_refresh_token(user.id, user.token_version)
        await self._store_refresh_jti(user.id, jti)
        return access, refresh

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

    async def _store_refresh_jti(self, user_id: UUID, jti: str) -> None:
        key = f"refresh:{user_id}:{jti}"
        ttl_seconds = 60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS
        await redis_client.set(key, "1", ex=ttl_seconds)

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
