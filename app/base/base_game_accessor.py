from abc import abstractmethod
from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.config import Config
from app.databases import Databases


class BaseGameAccessor(BaseAccessor):
    def __init__(self, databases: Databases, config: Config):
        super().__init__(databases, config)

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def set_state(self, chat: int, state: int) -> None:
        pass

    @abstractmethod
    async def get_state(self, chat: int, default: Optional[int] = None) -> Optional[int]:
        pass

    @abstractmethod
    async def reset_state(self, chat: int) -> None:
        pass

    @abstractmethod
    async def set_data(self, chat: int, data: dict) -> None:
        pass

    @abstractmethod
    async def get_data(self, chat: int, default: Optional[dict] = None) -> Optional[dict]:
        pass

    @abstractmethod
    async def update_data(self, chat: int, data: dict) -> None:
        pass

    @abstractmethod
    async def reset_data(self, chat: int) -> None:
        pass
