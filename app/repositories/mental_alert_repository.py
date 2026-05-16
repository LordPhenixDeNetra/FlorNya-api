from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mental_alert import MentalAlert, MentalAlertType


class MentalAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: UUID, alert_type: MentalAlertType) -> MentalAlert:
        alert = MentalAlert(user_id=user_id, alert_type=alert_type)
        self.session.add(alert)
        return alert

    async def list_unresolved(self, user_id: UUID) -> list[MentalAlert]:
        result = await self.session.execute(
            select(MentalAlert)
            .where(MentalAlert.user_id == user_id, MentalAlert.is_resolved == False)  # noqa: E712
            .order_by(MentalAlert.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest(self, user_id: UUID, alert_type: MentalAlertType) -> MentalAlert | None:
        result = await self.session.execute(
            select(MentalAlert)
            .where(MentalAlert.user_id == user_id, MentalAlert.alert_type == alert_type)
            .order_by(MentalAlert.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
