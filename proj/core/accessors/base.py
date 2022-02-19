import abc
from abc import abstractmethod
from typing import Optional

from proj.store import CoreStore
from proj.store.base.accessor import Accessor


class BaseGameAccessor(Accessor[CoreStore, None], metaclass=abc.ABCMeta):
    @abstractmethod
    async def set_state(self, chat: int, state: int) -> None:
        pass

    @abstractmethod
    async def get_state(
        self, chat: int, default: Optional[int] = None
    ) -> Optional[int]:
        pass

    @abstractmethod
    async def reset_state(self, chat: int) -> None:
        pass

    @abstractmethod
    async def set_data(self, chat: int, data: dict) -> None:
        pass

    @abstractmethod
    async def get_data(
        self, chat: int, default: Optional[dict] = None
    ) -> Optional[dict]:
        pass

    @abstractmethod
    async def update_data(self, chat: int, data: dict) -> None:
        pass

    @abstractmethod
    async def reset_data(self, chat: int) -> None:
        pass
