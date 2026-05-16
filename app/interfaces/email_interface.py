from abc import ABC, abstractmethod


class IEmailService(ABC):
    @abstractmethod
    async def send_password_reset(self, *, to_email: str, token: str, first_name: str | None) -> None: ...

    @abstractmethod
    async def send_welcome(self, *, to_email: str, first_name: str | None) -> None: ...
