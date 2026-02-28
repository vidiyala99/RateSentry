from abc import ABC, abstractmethod

class BaseLimiter(ABC):
    @abstractmethod
    async def is_allowed(self, key: str) -> tuple:
        pass
