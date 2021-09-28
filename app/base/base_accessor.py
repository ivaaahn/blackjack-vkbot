from abc import ABCMeta, abstractmethod
from logging import getLogger

from app.config import Config
from app.databases import Databases


class BaseAccessor(metaclass=ABCMeta):
    def __init__(self, databases: Databases, config: Config):
        self.databases = databases
        self.config = config
        self.logger = getLogger("accessor")

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass
