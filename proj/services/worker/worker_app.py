import asyncio
from typing import Mapping, Optional, Iterable

from proj.base.app import BaseApplication, run_nonserver_app
from proj.core.routes import setup_routes
from proj.store import Store
from proj.store.base.accessor import ConnectAccessor
from .worker import Worker

__all__ = (
    "WorkerApplication",
    "create_app",
    "run_worker",
)


class WorkerApplication(BaseApplication):
    class Meta:
        name = "worker"

    def __init__(self, config: Mapping, *args, **kwargs) -> None:
        super().__init__(config, *args, **kwargs)
        self._worker: Optional[Worker] = None

        setup_routes()

        self.on_startup.append(self.worker_connect)
        self.on_shutdown.append(self.worker_disconnect)

    async def worker_connect(self) -> None:
        self.logger.info("Connecting to worker...")
        self._worker = self.make_worker()
        await self._worker.start()

    async def worker_disconnect(self) -> None:
        self.logger.info("Disconnecting from worker...")
        await self._worker.stop()

    def make_worker(self) -> Worker:
        return Worker(self.store)

    def make_store(self) -> Store:
        return Store(config=self.config["store"])

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        yield self.store.rabbit
        yield self.store.vk
        yield self.store.game_settings
        yield self.store.players


def create_app(config: Mapping) -> WorkerApplication:
    return WorkerApplication(config)


def run_worker(app: WorkerApplication) -> None:
    asyncio.run(run_nonserver_app(app))
