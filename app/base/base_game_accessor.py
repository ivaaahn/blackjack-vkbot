import typing
from abc import ABCMeta, abstractmethod
from typing import Optional

from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BaseGameAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        super().__init__(app)

    @property
    @abstractmethod
    def db(self):
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
