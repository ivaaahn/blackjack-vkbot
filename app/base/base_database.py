from abc import ABCMeta, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.web.app import Application


class BaseDatabase(metaclass=ABCMeta):
    def __init__(self, app: "Application") -> None:
        self.app = app
        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)

    @abstractmethod
    async def connect(self, app: "Application") -> None:
        return

    @abstractmethod
    async def disconnect(self, app: "Application") -> None:
        return
