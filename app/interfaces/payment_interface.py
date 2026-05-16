from abc import ABC, abstractmethod
from uuid import UUID


class IPaymentService(ABC):
    @abstractmethod
    async def create_checkout_session(self, user_id: UUID, plan: str) -> str: ...

    @abstractmethod
    async def create_billing_portal(self, stripe_customer_id: str) -> str: ...

    @abstractmethod
    async def handle_webhook(self, payload: bytes, sig_header: str) -> None: ...
