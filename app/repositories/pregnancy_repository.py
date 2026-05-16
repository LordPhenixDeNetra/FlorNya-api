from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.breastfeeding_session import BreastfeedingSession
from app.models.epds_assessment import EPDSAssessment
from app.models.pregnancy_appointment import PregnancyAppointment
from app.models.pregnancy_profile import PregnancyProfile
from app.models.pregnancy_symptom_log import PregnancySymptomLog
from app.repositories.base import BaseRepository


class PregnancyProfileRepository(BaseRepository[PregnancyProfile]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=PregnancyProfile)

    async def get_by_user(self, user_id: UUID) -> PregnancyProfile | None:
        result = await self.session.execute(
            select(PregnancyProfile).where(PregnancyProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()


class PregnancySymptomRepository(BaseRepository[PregnancySymptomLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=PregnancySymptomLog)

    async def get_by_user_date(self, user_id: UUID, log_date: date) -> PregnancySymptomLog | None:
        result = await self.session.execute(
            select(PregnancySymptomLog).where(
                PregnancySymptomLog.user_id == user_id,
                PregnancySymptomLog.log_date == log_date,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, user_id: UUID, log_date: date, **fields: object) -> PregnancySymptomLog:
        existing = await self.get_by_user_date(user_id, log_date)
        if existing is not None:
            for k, v in fields.items():
                if v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing
        entity = PregnancySymptomLog(user_id=user_id, log_date=log_date, **fields)
        return await self.add(entity)

    async def list_range(
        self, *, user_id: UUID, date_from: date | None, date_to: date | None
    ) -> list[PregnancySymptomLog]:
        stmt = select(PregnancySymptomLog).where(PregnancySymptomLog.user_id == user_id)
        if date_from:
            stmt = stmt.where(PregnancySymptomLog.log_date >= date_from)
        if date_to:
            stmt = stmt.where(PregnancySymptomLog.log_date <= date_to)
        result = await self.session.execute(stmt.order_by(PregnancySymptomLog.log_date.desc()))
        return list(result.scalars().all())


class AppointmentRepository(BaseRepository[PregnancyAppointment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=PregnancyAppointment)

    async def list_by_user(self, user_id: UUID) -> list[PregnancyAppointment]:
        result = await self.session.execute(
            select(PregnancyAppointment)
            .where(PregnancyAppointment.user_id == user_id)
            .order_by(PregnancyAppointment.appointment_date.asc())
        )
        return list(result.scalars().all())

    async def list_upcoming(self, user_id: UUID, from_date: date) -> list[PregnancyAppointment]:
        result = await self.session.execute(
            select(PregnancyAppointment)
            .where(
                PregnancyAppointment.user_id == user_id,
                PregnancyAppointment.appointment_date >= from_date,
            )
            .order_by(PregnancyAppointment.appointment_date.asc())
        )
        return list(result.scalars().all())


class BreastfeedingRepository(BaseRepository[BreastfeedingSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=BreastfeedingSession)

    async def list_by_user_date(
        self, user_id: UUID, session_date: date
    ) -> list[BreastfeedingSession]:
        result = await self.session.execute(
            select(BreastfeedingSession)
            .where(
                BreastfeedingSession.user_id == user_id,
                BreastfeedingSession.session_date == session_date,
            )
            .order_by(BreastfeedingSession.started_at.asc())
        )
        return list(result.scalars().all())

    async def list_range(
        self, *, user_id: UUID, date_from: date | None, date_to: date | None
    ) -> list[BreastfeedingSession]:
        stmt = select(BreastfeedingSession).where(BreastfeedingSession.user_id == user_id)
        if date_from:
            stmt = stmt.where(BreastfeedingSession.session_date >= date_from)
        if date_to:
            stmt = stmt.where(BreastfeedingSession.session_date <= date_to)
        result = await self.session.execute(stmt.order_by(BreastfeedingSession.session_date.desc()))
        return list(result.scalars().all())


class EPDSRepository(BaseRepository[EPDSAssessment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=EPDSAssessment)

    async def get_latest(self, user_id: UUID) -> EPDSAssessment | None:
        result = await self.session.execute(
            select(EPDSAssessment)
            .where(EPDSAssessment.user_id == user_id)
            .order_by(EPDSAssessment.assessment_date.desc())
        )
        return result.scalars().first()

    async def list_by_user(self, user_id: UUID) -> list[EPDSAssessment]:
        result = await self.session.execute(
            select(EPDSAssessment)
            .where(EPDSAssessment.user_id == user_id)
            .order_by(EPDSAssessment.assessment_date.desc())
        )
        return list(result.scalars().all())
