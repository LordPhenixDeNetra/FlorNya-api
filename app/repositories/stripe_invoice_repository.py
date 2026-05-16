from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stripe_invoice import StripeInvoice
from app.repositories.base import BaseRepository


class StripeInvoiceRepository(BaseRepository[StripeInvoice]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=StripeInvoice)

    async def get_by_stripe_id(self, stripe_invoice_id: str) -> StripeInvoice | None:
        result = await self.session.execute(
            select(StripeInvoice).where(StripeInvoice.stripe_invoice_id == stripe_invoice_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[StripeInvoice], int]:
        stmt = select(StripeInvoice).where(StripeInvoice.user_id == user_id)
        total = await self.count(stmt)
        stmt = stmt.order_by(StripeInvoice.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total
