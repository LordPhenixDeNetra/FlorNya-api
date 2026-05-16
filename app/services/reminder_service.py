from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.reminder_config import ReminderConfig
from app.models.reminder_config import ReminderType as ReminderTypeModel
from app.models.user import User
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.reminder import ReminderConfigCreate, ReminderConfigPublic
from app.schemas.reminder import ReminderType as ReminderTypeSchema


class ReminderService:
    def __init__(self, session: AsyncSession, reminders: ReminderRepository):
        self.session = session
        self.reminders = reminders

    async def upsert_reminder(
        self, user: User, reminder_type: ReminderTypeSchema, data: ReminderConfigCreate
    ) -> ReminderConfigPublic:
        model_type = ReminderTypeModel(reminder_type.value)
        existing = await self.reminders.get_by_user_type(user.id, model_type)

        if existing is not None:
            existing.is_enabled = data.is_enabled
            existing.time_of_day = data.time_of_day
            existing.label_encrypted = encrypt_sensitive(data.label)
            await self.session.flush()
            entity = existing
        else:
            entity = ReminderConfig(
                user_id=user.id,
                reminder_type=model_type,
                is_enabled=data.is_enabled,
                time_of_day=data.time_of_day,
                label_encrypted=encrypt_sensitive(data.label),
            )
            await self.reminders.add(entity)

        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_public(entity)

    async def list_reminders(self, user: User) -> list[ReminderConfigPublic]:
        items = await self.reminders.list_by_user(user.id)
        return [self._to_public(r) for r in items]

    async def delete_reminder(self, user: User, reminder_type: ReminderTypeSchema) -> None:
        model_type = ReminderTypeModel(reminder_type.value)
        existing = await self.reminders.get_by_user_type(user.id, model_type)
        if existing is None:
            raise ValueError("reminder_not_found")
        await self.session.delete(existing)
        await self.session.commit()

    def _to_public(self, entity: ReminderConfig) -> ReminderConfigPublic:
        return ReminderConfigPublic(
            id=entity.id,
            user_id=entity.user_id,
            reminder_type=ReminderTypeSchema(entity.reminder_type.value),
            is_enabled=entity.is_enabled,
            time_of_day=entity.time_of_day,
            label=decrypt_sensitive(entity.label_encrypted),
            created_at=entity.created_at,
        )
