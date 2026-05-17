from datetime import datetime, timezone

import stripe
import structlog

logger = structlog.get_logger(__name__)

_ALLOWED_WEBHOOK_EVENTS = frozenset({
    "invoice.payment_succeeded",
    "customer.subscription.updated",
    "customer.subscription.deleted",
})

_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300

from app.config import get_settings
from app.interfaces.email_interface import IEmailService
from app.models.stripe_invoice import StripeInvoice
from app.models.user import User, UserPlan
from app.repositories.stripe_invoice_repository import StripeInvoiceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.payment import (
    BillingPortalResponse,
    CheckoutSessionResponse,
    InvoicePublic,
    PlanName,
)
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()

_PLAN_DISPLAY = {
    UserPlan.essential: "Essential",
    UserPlan.bloom: "Bloom",
    UserPlan.bloom_pro: "Bloom Pro",
}

_PLAN_FEATURES: dict[UserPlan, list[str]] = {
    UserPlan.essential: [
        "Suivi de cycle illimité",
        "Journal d'humeur & symptômes",
        "Rappels personnalisés",
    ],
    UserPlan.bloom: [
        "Tout Essential",
        "Insights IA de votre cycle",
        "Calendrier de fertilité",
    ],
    UserPlan.bloom_pro: [
        "Tout Bloom",
        "Export PDF mensuel",
        "Assistance prioritaire",
    ],
}

_PLAN_PRICE_MAP = {
    PlanName.essential: settings.STRIPE_PRICE_ESSENTIAL,
    PlanName.bloom: settings.STRIPE_PRICE_BLOOM,
    PlanName.bloom_pro: settings.STRIPE_PRICE_BLOOM_PRO,
}

_PRICE_PLAN_MAP: dict[str, UserPlan] = {}


def _build_price_plan_map() -> dict[str, UserPlan]:
    return {
        settings.STRIPE_PRICE_ESSENTIAL: UserPlan.free,
        settings.STRIPE_PRICE_BLOOM: UserPlan.bloom,
        settings.STRIPE_PRICE_BLOOM_PRO: UserPlan.bloom_pro,
    }


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        invoices: StripeInvoiceRepository,
        email_service: IEmailService | None = None,
    ):
        self.session = session
        self.users = users
        self.invoices = invoices
        self.email_service = email_service
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def _get_or_create_customer(self, user: User) -> str:
        if user.stripe_customer_id:
            return user.stripe_customer_id

        customer = stripe.Customer.create(
            email=user.email,
            name=user.first_name or user.email,
            metadata={"user_id": str(user.id)},
        )
        user.stripe_customer_id = customer["id"]
        await self.session.commit()
        return customer["id"]

    async def create_checkout_session(
        self, user: User, plan: PlanName, success_url: str, cancel_url: str
    ) -> CheckoutSessionResponse:
        customer_id = await self._get_or_create_customer(user)
        price_id = _PLAN_PRICE_MAP[plan]

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user.id), "plan": plan.value},
        )
        return CheckoutSessionResponse(
            checkout_url=session["url"],
            session_id=session["id"],
        )

    async def create_billing_portal(self, user: User, return_url: str) -> BillingPortalResponse:
        customer_id = await self._get_or_create_customer(user)
        portal = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return BillingPortalResponse(portal_url=portal["url"])

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
                tolerance=_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS,
            )
        except (stripe.error.SignatureVerificationError, ValueError):
            raise ValueError("invalid_webhook_signature")

        event_type = event["type"]
        if event_type not in _ALLOWED_WEBHOOK_EVENTS:
            logger.debug("stripe.webhook.ignored", event_type=event_type, event_id=event["id"])
            return

        data = event["data"]["object"]
        logger.info("stripe.webhook.processing", event_type=event_type, event_id=event["id"])

        if event_type == "invoice.payment_succeeded":
            await self._handle_invoice_succeeded(data)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data)

    async def _handle_invoice_succeeded(self, invoice: dict) -> None:
        stripe_invoice_id = invoice["id"]
        existing = await self.invoices.get_by_stripe_id(stripe_invoice_id)
        if existing is not None:
            return

        customer_id = invoice.get("customer")
        if not customer_id:
            return
        user = await self.users.get_by_stripe_customer_id(customer_id)
        if user is None:
            return

        period_start = invoice.get("period_start")
        period_end = invoice.get("period_end")

        entity = StripeInvoice(
            user_id=user.id,
            stripe_invoice_id=stripe_invoice_id,
            amount_cents=invoice.get("amount_paid", 0),
            currency=invoice.get("currency", "eur"),
            status=invoice.get("status", "paid"),
            invoice_pdf_url=invoice.get("invoice_pdf"),
            period_start=datetime.fromtimestamp(period_start, tz=timezone.utc) if period_start else None,
            period_end=datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None,
        )
        await self.invoices.add(entity)

        subscription_id = invoice.get("subscription")
        if subscription_id:
            user.stripe_subscription_id = subscription_id

        new_plan: UserPlan | None = None
        lines = invoice.get("lines", {}).get("data", [])
        for line in lines:
            price_id = line.get("price", {}).get("id")
            if price_id:
                plan_map = _build_price_plan_map()
                new_plan = plan_map.get(price_id)
                if new_plan:
                    user.plan = new_plan
                    break

        await self.session.commit()

        if new_plan and self.email_service and new_plan in _PLAN_FEATURES:
            await self.email_service.send_subscription_confirmed(
                to_email=user.email,
                first_name=user.first_name,
                plan_name=_PLAN_DISPLAY.get(new_plan, new_plan.value.title()),
                plan_features=_PLAN_FEATURES[new_plan],
            )

    async def _handle_subscription_updated(self, subscription: dict) -> None:
        customer_id = subscription.get("customer")
        if not customer_id:
            return
        user = await self.users.get_by_stripe_customer_id(customer_id)
        if user is None:
            return

        items = subscription.get("items", {}).get("data", [])
        plan_map = _build_price_plan_map()
        for item in items:
            price_id = item.get("price", {}).get("id")
            new_plan = plan_map.get(price_id or "")
            if new_plan:
                user.plan = new_plan
                break

        user.stripe_subscription_id = subscription["id"]
        await self.session.commit()

    async def _handle_subscription_deleted(self, subscription: dict) -> None:
        customer_id = subscription.get("customer")
        if not customer_id:
            return
        user = await self.users.get_by_stripe_customer_id(customer_id)
        if user is None:
            return
        user.plan = UserPlan.free
        user.stripe_subscription_id = None
        await self.session.commit()

    async def list_invoices(
        self, user: User, skip: int = 0, limit: int = 20
    ) -> PaginatedResponse[InvoicePublic]:
        items, total = await self.invoices.list_by_user(user.id, skip=skip, limit=limit)
        public_items = [
            InvoicePublic(
                id=inv.id,
                stripe_invoice_id=inv.stripe_invoice_id,
                amount_cents=inv.amount_cents,
                currency=inv.currency,
                status=inv.status,
                invoice_pdf_url=inv.invoice_pdf_url,
                period_start=inv.period_start,
                period_end=inv.period_end,
                created_at=inv.created_at,
            )
            for inv in items
        ]
        has_more = skip + len(public_items) < total
        return PaginatedResponse(
            items=public_items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=has_more,
        )
