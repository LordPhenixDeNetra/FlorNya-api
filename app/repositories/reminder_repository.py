from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder_config import ReminderConfig, ReminderType
from app.repositories.base import BaseRepository


class ReminderRepository(BaseRepository[ReminderConfig]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ReminderConfig)

    async def get_by_user_type(
        self, user_id: UUID, reminder_type: ReminderType
    ) -> ReminderConfig | None:
        result = await self.session.execute(
            select(ReminderConfig).where(
                ReminderConfig.user_id == user_id,
                ReminderConfig.reminder_type == reminder_type,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[ReminderConfig]:
        result = await self.session.execute(
            select(ReminderConfig).where(ReminderConfig.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_enabled_by_type(self, reminder_type: ReminderType) -> list[ReminderConfig]:
        result = await self.session.execute(
            select(ReminderConfig).where(
                ReminderConfig.reminder_type == reminder_type,
                ReminderConfig.is_enabled.is_(True),
            )
        )
        return list(result.scalars().all())
