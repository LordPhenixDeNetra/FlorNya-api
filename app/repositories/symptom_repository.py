from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.symptom_log import SymptomLog
from app.repositories.base import BaseRepository


class SymptomRepository(BaseRepository[SymptomLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=SymptomLog)

    async def get_by_user_date(self, user_id: UUID, log_date: date) -> SymptomLog | None:
        result = await self.session.execute(
            select(SymptomLog).where(
                SymptomLog.user_id == user_id, SymptomLog.log_date == log_date
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, user_id: UUID, log_date: date, **fields: object) -> SymptomLog:
        existing = await self.get_by_user_date(user_id, log_date)
        if existing is not None:
            for k, v in fields.items():
                if v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        entity = SymptomLog(user_id=user_id, log_date=log_date, **fields)
        return await self.add(entity)

    async def list_range(
        self, *, user_id: UUID, date_from: date | None, date_to: date | None
    ) -> list[SymptomLog]:
        stmt = select(SymptomLog).where(SymptomLog.user_id == user_id)
        if date_from is not None:
            stmt = stmt.where(SymptomLog.log_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(SymptomLog.log_date <= date_to)
        stmt = stmt.order_by(SymptomLog.log_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_dates_with_symptoms(self, user_id: UUID, dates: list[date]) -> set[date]:
        if not dates:
            return set()
        stmt = select(SymptomLog.log_date).where(
            SymptomLog.user_id == user_id, SymptomLog.log_date.in_(dates)
        )
        result = await self.session.execute(stmt)
        return {row[0] for row in result.all()}
