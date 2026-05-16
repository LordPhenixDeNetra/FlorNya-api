from abc import ABC, abstractmethod


class INotifier(ABC):
    @abstractmethod
    async def send(self, *, user_id: str, message: str, payload: dict, language: str = "fr") -> bool: ...
