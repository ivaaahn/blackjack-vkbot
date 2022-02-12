import asyncio
import weakref
from asyncio import Task, CancelledError, get_event_loop
from typing import Optional, Mapping, Type, Generic, TypeVar

from proj.poller.errors import PollerError
from proj.store import PollerStore
from proj.store.base import S
from proj.config import ConfigType
from proj.store.base.accessor import ConnectAccessor


API = TypeVar("API", bound=ConnectAccessor)


class AbstractPoller(ConnectAccessor[PollerStore, None], Generic[API]):
    class Meta:
        name = "poller"

    def __init__(
        self,
        store: PollerStore,
        api: API,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = None,
    ) -> None:
        super().__init__(store, name=name, config=config, config_type=config_type)

        self._api: API = api

        self._is_running = False
        self._poll_task: Optional[Task] = None

    @property
    def api(self) -> API:
        return self._api

    @staticmethod
    def _handle_task_result(task: Task) -> None:
        try:
            task.result()
        except CancelledError:
            pass
        except Exception:
            raise

    async def _poller_connect(self):
        await self._api._connect()
        self.logger.info(f"Poller.{self.name} connected to API")
        self._is_running = True

        self._poll_task = asyncio.create_task(self._poll())
        self._poll_task.add_done_callback(self._handle_task_result)

    async def _poller_disconnect(self) -> None:
        if self._poll_task and self._is_running:
            self._is_running = False

            if self._poll_task.done():
                self.logger.error(
                    f"Poll task already done! It may be is a result of exception: {self._poll_task.exception()}"
                )
                return

            self.logger.debug(
                "Poll task is not done, therefore it gonna be cancelled..."
            )

            self._poll_task.cancel()

            try:
                await asyncio.gather(self._poll_task)
            except CancelledError:
                self._logger.info(f"Poller.{self._name}'s task was cancelled")

        await self.api._disconnect()
        self.logger.info(f"Poller.{self.name} disconnected from API")

    async def _connect(self) -> None:
        await self._poller_connect()

    async def _disconnect(self) -> None:
        await self._poller_disconnect()

    async def _poll(self):
        self._logger.info(f"Poller {self._name} started")
