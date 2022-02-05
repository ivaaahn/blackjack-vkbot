import asyncio
from logging import getLogger
from typing import Mapping, Iterable, Optional

from aiohttp.web_runner import GracefulExit

from proj.base.app import BaseApplication, NonServerAppRunner, run_nonserver_app
from proj.services.poller.base import AbstractPoller
from proj.services.poller.vk_poller import VkPoller
from proj.store import Store
from proj.store.base.accessor import ConnectAccessor

__all__ = (
    "PollerApplication",
    "run_poller",
    "create_app",
)


class PollerApplication(BaseApplication):
    class Meta:
        name = "poller"

    def __init__(self, config: Mapping, *args, **kwargs) -> None:
        super().__init__(config, *args, **kwargs)
        self._poller: Optional[AbstractPoller] = None

        self.on_startup.append(self.poller_connect)
        self.on_shutdown.append(self.poller_disconnect)

    async def poller_connect(self) -> None:
        self.logger.info("Connecting to poller...")
        self._poller = self.make_poller()
        await self._poller.start()

    async def poller_disconnect(self) -> None:
        self.logger.info("Disconnecting from poller...")
        await self._poller.stop()

    def make_poller(self) -> AbstractPoller:
        return VkPoller(self.store)

    def make_store(self) -> Store:
        return Store(config=self.config["store"])

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        yield self.store.rabbit


def create_app(config: Mapping) -> PollerApplication:
    return PollerApplication(config)


def run_poller(app: PollerApplication) -> None:
    asyncio.run(run_nonserver_app(app))
