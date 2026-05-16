import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import PaginationParams


class PlanName(str, enum.Enum):
    essential = "essential"
    bloom = "bloom"
    bloom_pro = "bloom_pro"


class CheckoutRequest(BaseModel):
    plan: PlanName


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class BillingPortalResponse(BaseModel):
    portal_url: str


class InvoicePublic(BaseModel):
    id: UUID
    stripe_invoice_id: str
    amount_cents: int
    currency: str
    status: str
    invoice_pdf_url: str | None
    period_start: datetime | None
    period_end: datetime | None
    created_at: datetime


class InvoiceFilterParams(PaginationParams):
    pass
