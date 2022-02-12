import asyncio
from typing import Mapping, Optional, Iterable

from proj.base.application import BaseApplication, run_nonserver_app
from proj.core.routes import setup_routes
from proj.store import CoreStore
from proj.store.base.accessor import ConnectAccessor
from .worker import GameRequestReceiver

__all__ = (
    "CoreApplication",
    "create_app",
    "run_worker",
)

from ..logger import LoggerFactory


class CoreApplication(BaseApplication[CoreStore]):
    class Meta:
        name = "worker"

    def __init__(
        self, config: Mapping, logger_factory: LoggerFactory, **kwargs
    ) -> None:
        super().__init__(config, logger_factory, **kwargs)
        self._worker: Optional[GameRequestReceiver] = None

        setup_routes()

    #     self.on_startup.append(self.worker_connect)
    #     self.on_shutdown.append(self.worker_disconnect)
    #
    # async def worker_connect(self) -> None:
    #     self.logger.info("Connecting to worker...")
    #     self._worker = self.make_worker()
    #     await self._worker.start()
    #
    # async def worker_disconnect(self) -> None:
    #     self.logger.info("Disconnecting from worker...")
    #     await self._worker.stop()

    # def make_worker(self) -> Worker:
    #     return Worker(self.store)

    def make_store(self) -> CoreStore:
        return CoreStore(self, config=self.config["store"])

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        yield self.store.mongo
        yield self.store.rmq_worker
        yield self.store.vk
        yield self.store.game_settings
        yield self.store.players
        yield self.store.redis


def create_app(config: Mapping, logger_factory: LoggerFactory) -> CoreApplication:
    return CoreApplication(config, logger_factory)


def run_worker(app: CoreApplication) -> None:
    run_nonserver_app(app)
