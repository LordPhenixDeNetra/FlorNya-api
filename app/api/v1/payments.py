from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.deps import get_current_user, get_payment_service
from app.config import get_settings
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.payment import (
    BillingPortalResponse,
    CheckoutRequest,
    CheckoutSessionResponse,
    InvoiceFilterParams,
    InvoicePublic,
)
from app.services.payment_service import PaymentService

router = APIRouter()
settings = get_settings()


@router.post("/checkout", response_model=CheckoutSessionResponse)
@limiter.limit("10/minute")
async def create_checkout(
    request: Request,
    data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> CheckoutSessionResponse:
    success_url = f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.FRONTEND_URL}/payment/cancel"
    return await service.create_checkout_session(current_user, data.plan, success_url, cancel_url)


@router.post("/portal", response_model=BillingPortalResponse)
@limiter.limit("10/minute")
async def create_portal(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> BillingPortalResponse:
    return_url = f"{settings.FRONTEND_URL}/settings/billing"
    return await service.create_billing_portal(current_user, return_url)


@router.post("/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    payload = await request.body()
    try:
        await service.handle_webhook(payload, stripe_signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_webhook")
    return {"received": True}


@router.get("/invoices", response_model=PaginatedResponse[InvoicePublic])
@limiter.limit("30/minute")
async def list_invoices(
    request: Request,
    params: InvoiceFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
) -> PaginatedResponse[InvoicePublic]:
    return await service.list_invoices(current_user, skip=params.skip, limit=params.limit)
