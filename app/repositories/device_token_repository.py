from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_token import DevicePlatform, DeviceToken


class DeviceTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, user_id: UUID, token: str, platform: DevicePlatform) -> DeviceToken:
        result = await self.session.execute(
            select(DeviceToken).where(
                DeviceToken.user_id == user_id,
                DeviceToken.token == token,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.is_active = True
            existing.platform = platform
            return existing

        device_token = DeviceToken(user_id=user_id, token=token, platform=platform, is_active=True)
        self.session.add(device_token)
        return device_token

    async def deactivate(self, user_id: UUID, token: str) -> None:
        await self.session.execute(
            update(DeviceToken)
            .where(DeviceToken.user_id == user_id, DeviceToken.token == token)
            .values(is_active=False)
        )

    async def list_active_by_user(self, user_id: UUID) -> list[DeviceToken]:
        result = await self.session.execute(
            select(DeviceToken).where(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def delete_all_for_user(self, user_id: UUID) -> None:
        await self.session.execute(delete(DeviceToken).where(DeviceToken.user_id == user_id))
