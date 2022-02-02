import asyncio
import inspect
import logging
import weakref
from logging import getLogger
from typing import Generic, TypeVar, Optional, Mapping, Type, Set, Callable, Awaitable

S = TypeVar("S")
ConfigType = TypeVar("ConfigType")
CallbackType = Callable[[], Awaitable[None]]


class BaseAccessor(Generic[S, ConfigType]):
    class Meta:
        name = None

    def __init__(
        self,
        store: S,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = None,
    ):
        self._store = weakref.ref(store)
        self._name = name or self.Meta.name or self.__class__.__name__
        self._name_is_custom = name is not None
        self._raw_config = config or store.config.get(self._name) or {}

        try:
            self._config = config_type(**self._raw_config) if config_type else None
        except Exception as err:
            raise ValueError(
                f"Error parsing config of {self._name} accessor: {str(err)}"
            ) from err

        self._logger = getLogger(f"accessor.{self._name}")

    @property
    def store(self) -> S:
        return self._store()

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.store.loop

    @property
    def raw_config(self) -> Mapping:
        return self._raw_config

    @property
    def config(self) -> ConfigType:
        return self._config


class ConnectAccessor(BaseAccessor[S, ConfigType]):
    def __init__(
        self,
        store: S,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = None,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)

        self._connect_lock = asyncio.Lock(loop=self.loop)
        self._disconnect_lock = asyncio.Lock(loop=self.loop)
        self._event = asyncio.Event(loop=self.loop)
        self._connected = False
        self._connect_callbacks: Set[CallbackType] = set()
        self._disconnect_callbacks: Set[CallbackType] = set()

    def add_on_connect(self, cb: CallbackType):
        self._connect_callbacks.add(cb)

    def add_on_disconnect(self, cb: CallbackType):
        self._disconnect_callbacks.add(cb)

    async def connect(self):
        async with self._connect_lock:
            if self._connected:
                return

            if inspect.iscoroutinefunction(self._connect):
                await self._connect()
            else:
                # noinspection PyAsyncCall
                self._connect()

            for cb in self._connect_callbacks:
                await cb()

            self._connected = True
            self._event.set()
            self.logger.info(f'Connected to {self.name} accessor')

    async def disconnect(self):
        async with self._disconnect_lock:
            if not self._connected:
                return

            if inspect.iscoroutinefunction(self._disconnect):
                await self._disconnect()
            else:
                # noinspection PyAsyncCall
                self._disconnect()

            for cb in self._disconnect_callbacks:
                await cb()

            self._connected = False
            self._event.clear()
            self.logger.info(f'Disconnected from {self.name} accessor')

    async def _connect(self):
        pass

    async def _disconnect(self):
        pass

    async def wait_connected(self) -> bool:
        return await self._event.wait()

    @property
    def is_connected(self) -> bool:
        return self._connected
