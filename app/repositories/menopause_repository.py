from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menopause_log import MenopauseLog
from app.repositories.base import BaseRepository


class MenopauseRepository(BaseRepository[MenopauseLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=MenopauseLog)

    async def get_by_user_date(self, user_id: UUID, log_date: date) -> MenopauseLog | None:
        result = await self.session.execute(
            select(MenopauseLog).where(
                MenopauseLog.user_id == user_id, MenopauseLog.log_date == log_date
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, user_id: UUID, log_date: date, **fields: object) -> MenopauseLog:
        existing = await self.get_by_user_date(user_id, log_date)
        if existing is not None:
            for k, v in fields.items():
                if v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing
        entity = MenopauseLog(user_id=user_id, log_date=log_date, **fields)
        return await self.add(entity)

    async def list_range(
        self, *, user_id: UUID, date_from: date | None, date_to: date | None
    ) -> list[MenopauseLog]:
        stmt = select(MenopauseLog).where(MenopauseLog.user_id == user_id)
        if date_from:
            stmt = stmt.where(MenopauseLog.log_date >= date_from)
        if date_to:
            stmt = stmt.where(MenopauseLog.log_date <= date_to)
        result = await self.session.execute(stmt.order_by(MenopauseLog.log_date.desc()))
        return list(result.scalars().all())

    async def avg_hot_flash_per_day(self, user_id: UUID, days: int = 30) -> float | None:
        from datetime import date as date_type
        from datetime import timedelta

        cutoff = date_type.today() - timedelta(days=days)
        result = await self.session.execute(
            select(func.avg(MenopauseLog.hot_flash_count)).where(
                MenopauseLog.user_id == user_id,
                MenopauseLog.log_date >= cutoff,
                MenopauseLog.hot_flash_count.isnot(None),
            )
        )
        val = result.scalar_one_or_none()
        return float(val) if val is not None else None
