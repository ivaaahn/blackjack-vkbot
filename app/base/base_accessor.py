import typing
from abc import ABCMeta, abstractmethod
from logging import getLogger

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BaseAccessor(metaclass=ABCMeta):
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("accessor")
        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)

    @abstractmethod
    async def connect(self, app: "Application"):
        pass

    @abstractmethod
    async def disconnect(self, app: "Application"):
        pass
