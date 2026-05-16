from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nutrition_log import NutritionLog
from app.repositories.base import BaseRepository


class NutritionRepository(BaseRepository[NutritionLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=NutritionLog)

    async def get_by_user_date(self, user_id: UUID, log_date: date) -> NutritionLog | None:
        result = await self.session.execute(
            select(NutritionLog).where(
                NutritionLog.user_id == user_id, NutritionLog.log_date == log_date
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, user_id: UUID, log_date: date, **fields: object) -> NutritionLog:
        existing = await self.get_by_user_date(user_id, log_date)
        if existing is not None:
            for k, v in fields.items():
                if v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing
        entity = NutritionLog(user_id=user_id, log_date=log_date, **fields)
        return await self.add(entity)

    async def list_range(
        self, *, user_id: UUID, date_from: date | None, date_to: date | None
    ) -> list[NutritionLog]:
        stmt = select(NutritionLog).where(NutritionLog.user_id == user_id)
        if date_from:
            stmt = stmt.where(NutritionLog.log_date >= date_from)
        if date_to:
            stmt = stmt.where(NutritionLog.log_date <= date_to)
        result = await self.session.execute(stmt.order_by(NutritionLog.log_date.desc()))
        return list(result.scalars().all())
