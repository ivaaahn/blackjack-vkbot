from typing import Optional, TYPE_CHECKING
from abc import ABCMeta, abstractmethod
from logging import getLogger

if TYPE_CHECKING:
    from app.app import Application


class BaseAccessor(metaclass=ABCMeta):
    def __init__(self, app: Optional["Application"]):
        self.app = app
        self.logger = getLogger("accessor")

        if app is not None:
            app.on_startup.append(self.connect)
            app.on_cleanup.append(self.disconnect)

    @abstractmethod
    async def connect(self, app: "Application") -> None:
        pass

    @abstractmethod
    async def disconnect(self, app: "Application") -> None:
        pass
