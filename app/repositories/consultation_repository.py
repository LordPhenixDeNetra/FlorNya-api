from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation_booking import ConsultationBooking, ConsultationStatus


class ConsultationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: UUID, **kwargs) -> ConsultationBooking:
        booking = ConsultationBooking(user_id=user_id, **kwargs)
        self.session.add(booking)
        return booking

    async def list_by_user(self, user_id: UUID, limit: int = 10) -> list[ConsultationBooking]:
        result = await self.session.execute(
            select(ConsultationBooking)
            .where(ConsultationBooking.user_id == user_id)
            .order_by(ConsultationBooking.scheduled_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, booking_id: UUID, user_id: UUID) -> ConsultationBooking | None:
        result = await self.session.execute(
            select(ConsultationBooking).where(
                ConsultationBooking.id == booking_id, ConsultationBooking.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, booking_id: UUID, status: ConsultationStatus, preparation_notes_encrypted: str | None = None
    ) -> ConsultationBooking | None:
        booking = await self.get_by_id(booking_id, booking_id)
        if booking:
            booking.status = status
            if preparation_notes_encrypted:
                booking.preparation_notes_encrypted = preparation_notes_encrypted
        return booking
