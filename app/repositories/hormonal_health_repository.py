from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hormonal_treatment import HormonalTreatment
from app.models.pain_log import PainLog
from app.repositories.base import BaseRepository


class PainLogRepository(BaseRepository[PainLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=PainLog)

    async def get_by_user_date(self, user_id: UUID, log_date: date) -> PainLog | None:
        result = await self.session.execute(
            select(PainLog).where(PainLog.user_id == user_id, PainLog.log_date == log_date)
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, user_id: UUID, log_date: date, **fields: object) -> PainLog:
        existing = await self.get_by_user_date(user_id, log_date)
        if existing is not None:
            for k, v in fields.items():
                if v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing
        entity = PainLog(user_id=user_id, log_date=log_date, **fields)
        return await self.add(entity)

    async def list_range(
        self, *, user_id: UUID, date_from: date | None, date_to: date | None
    ) -> list[PainLog]:
        stmt = select(PainLog).where(PainLog.user_id == user_id)
        if date_from:
            stmt = stmt.where(PainLog.log_date >= date_from)
        if date_to:
            stmt = stmt.where(PainLog.log_date <= date_to)
        result = await self.session.execute(stmt.order_by(PainLog.log_date.desc()))
        return list(result.scalars().all())


class HormonalTreatmentRepository(BaseRepository[HormonalTreatment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=HormonalTreatment)

    async def list_by_user(self, user_id: UUID, active_only: bool = False) -> list[HormonalTreatment]:
        stmt = select(HormonalTreatment).where(HormonalTreatment.user_id == user_id)
        if active_only:
            stmt = stmt.where(HormonalTreatment.is_active.is_(True))
        result = await self.session.execute(stmt.order_by(HormonalTreatment.created_at.desc()))
        return list(result.scalars().all())

    async def deactivate_all(self, user_id: UUID) -> None:
        treatments = await self.list_by_user(user_id, active_only=True)
        for t in treatments:
            t.is_active = False
        await self.session.flush()
