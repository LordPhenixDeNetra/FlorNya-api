from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conception_attempt import ConceptionAttempt
from app.models.fertility_log import FertilityLog
from app.repositories.base import BaseRepository


class FertilityRepository(BaseRepository[FertilityLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=FertilityLog)

    async def get_by_user_date(self, user_id: UUID, log_date: date) -> FertilityLog | None:
        result = await self.session.execute(
            select(FertilityLog).where(
                FertilityLog.user_id == user_id, FertilityLog.log_date == log_date
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, user_id: UUID, log_date: date, **fields: object) -> FertilityLog:
        existing = await self.get_by_user_date(user_id, log_date)
        if existing is not None:
            for k, v in fields.items():
                if v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing
        entity = FertilityLog(user_id=user_id, log_date=log_date, **fields)
        return await self.add(entity)

    async def list_range(
        self, *, user_id: UUID, date_from: date | None, date_to: date | None
    ) -> list[FertilityLog]:
        stmt = select(FertilityLog).where(FertilityLog.user_id == user_id)
        if date_from:
            stmt = stmt.where(FertilityLog.log_date >= date_from)
        if date_to:
            stmt = stmt.where(FertilityLog.log_date <= date_to)
        stmt = stmt.order_by(FertilityLog.log_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ConceptionAttemptRepository(BaseRepository[ConceptionAttempt]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ConceptionAttempt)

    async def list_by_user(self, user_id: UUID) -> list[ConceptionAttempt]:
        result = await self.session.execute(
            select(ConceptionAttempt)
            .where(ConceptionAttempt.user_id == user_id)
            .order_by(ConceptionAttempt.attempt_date.desc())
        )
        return list(result.scalars().all())
