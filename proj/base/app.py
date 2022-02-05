import asyncio
import logging
import signal
from logging import getLogger
from typing import Mapping, Iterable, Optional

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_runner import AppRunner, _raise_graceful_exit, GracefulExit

from proj.services.app_logger import get_logger
from proj.store import Store
from proj.store.base import S
from proj.store.base.accessor import ConnectAccessor
from proj.store.base.connector import Connector


class BaseApplication(web.Application):
    class Meta:
        name = None

    def __init__(
        self, config: Mapping, *, name: Optional[str] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._config = config
        self._store = None
        self._connector = None
        self._name = name or self.Meta.name or self.__class__.__name__
        self.on_startup.append(self.store_connect)
        self.on_shutdown.append(self.store_disconnect)
        self.logger = get_logger('app')

    @property
    def config(self) -> Mapping:
        return self._config

    def _log_request(self, request: Request) -> None:
        r, query = request, None

        if r.query_string:
            query = "?" + r.query_string

        self.logger.info(f"Request {r.method}, {r.path}{query}")

    def _make_request(self, *args, **kwargs) -> Request:
        request = super()._make_request(*args, **kwargs)
        self._log_request(request)
        return request

    @property
    def store(self):
        return self._store

    @property
    def connector(self):
        return self._connector

    def make_store(self) -> S:
        pass

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        return ()

    def make_connector(self, store: Store) -> Connector:
        connector = Connector(store)

        for accessor in self.accessors:
            connector.add(accessor)

        return connector

    async def store_connect(self, _):
        self._store = self.make_store()
        self._connector = self.make_connector(self._store)

        self.logger.info("Starting store...")
        self.connector.connect_async()

    async def store_disconnect(self, _):
        self.logger.info("Stopping store...")
        await self.connector.disconnect()


class NonServerAppRunner(AppRunner):
    async def setup(self) -> None:
        loop = asyncio.get_event_loop()

        if self._handle_signals:
            loop.add_signal_handler(signal.SIGINT, _raise_graceful_exit)
            loop.add_signal_handler(signal.SIGTERM, _raise_graceful_exit)

        self._server = await self._make_server()

    async def _make_server(self) -> None:
        self._app.on_startup.freeze()
        await self._app.startup()
        self._app.freeze()


async def run_nonserver_app(app: BaseApplication):
    runner = NonServerAppRunner(app)
    await runner.setup()

    loop = asyncio.get_event_loop()
    logger = get_logger(__file__)

    try:
        main_task = loop.create_task(run_nonserver_app(app))
        runner = loop.run_until_complete(main_task)
        loop.run_forever()
    except (GracefulExit, KeyboardInterrupt):
        logger.info("KeyboardInterrupt")
    except Exception as err:
        logger.exception(f"Caught exception: {err}")
    finally:
        logger.info("Runner shutdown...")
        await runner.shutdown()
