from abc import ABCMeta, abstractmethod

from app.config import Config


class BaseDatabase(metaclass=ABCMeta):
    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    async def connect(self) -> None:
        return

    @abstractmethod
    async def disconnect(self) -> None:
        return
