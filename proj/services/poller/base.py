import asyncio
import weakref
from asyncio import Task
from logging import getLogger
from typing import Optional, Mapping, Type, Generic

from proj.services.app_logger import get_logger
from proj.store.base import S, ConfigType


class AbstractPoller(Generic[S, ConfigType]):
    class Meta:
        name = None

    def __init__(
        self,
        store: S,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = None,
    ) -> None:
        self._store = weakref.ref(store)
        self._name = name or self.Meta.name or self.__class__.__name__
        self._name_is_custom = name is not None
        self._raw_config = config or store.config.get(self._name) or {}
        self._parse_config(config_type)
        self._logger = get_logger(f"poller.{self._name}")

        self._is_running = False
        self._poll_task: Optional[Task] = None

    def _parse_config(self, config_type: Type[ConfigType]):
        try:
            self._config = config_type(**self._raw_config) if config_type else None
        except Exception as err:
            raise ValueError(
                f"Error parsing config of {self._name} accessor: {str(err)}"
            ) from err

    @property
    def store(self) -> S:
        return self._store

    async def start(self) -> None:
        self._logger.info(f"Poller {self._name} starting...")
        self._is_running = True
        self._poll_task = asyncio.create_task(self._poll())
        self._logger.info(f"Poller {self._name} started...")

    async def stop(self) -> None:
        self._logger.info(f"Poller {self._name} stopping...")
        if self._poll_task and self._is_running:
            self._is_running = False
            self._poll_task.cancel()

        self._logger.info("Poller stopped")

    async def _poll(self):
        self._logger.info(f"Poller {self._name} started")
