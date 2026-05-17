from abc import ABC, abstractmethod


class IEmailService(ABC):
    @abstractmethod
    async def send_password_reset(self, *, to_email: str, token: str, first_name: str | None) -> None: ...

    @abstractmethod
    async def send_welcome(self, *, to_email: str, first_name: str | None) -> None: ...

    @abstractmethod
    async def send_period_reminder(
        self, *, to_email: str, first_name: str | None, days_before: int, next_period_date: str
    ) -> None: ...

    @abstractmethod
    async def send_subscription_confirmed(
        self, *, to_email: str, first_name: str | None, plan_name: str, plan_features: list[str]
    ) -> None: ...
