import asyncio
import logging
import signal
import traceback
from asyncio import AbstractEventLoop
from typing import Mapping, Iterable, Optional, Generic, TypeVar

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_runner import AppRunner, _raise_graceful_exit, GracefulExit

from proj.logger import LoggerFactory
from proj.store.base.store import S
from proj.store.base.accessor import ConnectAccessor
from proj.store.base.connector import Connector


class BaseApplication(web.Application, Generic[S]):
    class Meta:
        name = None

    def __init__(
        self,
        config: Mapping,
        logger_factory: LoggerFactory,
        *,
        name: Optional[str] = None,
        **kwargs,
    ) -> None:

        super().__init__(**kwargs)
        self._config = config
        self._store = None
        self._connector = None
        self._name = name or self.Meta.name or self.__class__.__name__

        self.on_startup.append(self.store_connect)
        self.on_shutdown.append(self.store_disconnect)

        self._logger_factory = logger_factory
        self.logger = self.get_logger(f"Application.{self._name}")

    def get_logger(self, name: str) -> logging.Logger:
        return self._logger_factory.create(name)

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
    def store(self) -> S:
        return self._store

    @property
    def connector(self):
        return self._connector

    def make_store(self) -> S:
        pass

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        return ()

    def make_connector(self, store: S) -> Connector:
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

    async def shutdown_(self, logger, lp: AbstractEventLoop) -> None:
        logger.info("Shutting down...")
        await super().shutdown()
        lp.stop()


async def _run_nonserver_app(app: BaseApplication) -> NonServerAppRunner:
    runner = NonServerAppRunner(app)
    await runner.setup()
    return runner


def run_nonserver_app(app: BaseApplication):
    loop = asyncio.get_event_loop()
    logger = app.logger

    def handle_exception(lp, context):
        msg = context.get("exception", context["message"])
        logger.exception(f"[0]Caught exception: {msg}, {context}")
        asyncio.create_task(runner.shutdown_(logger, lp))

    runner: Optional[NonServerAppRunner] = None

    try:
        runner = loop.run_until_complete(_run_nonserver_app(app))
        loop.set_exception_handler(handle_exception)
        loop.run_forever()
    except (GracefulExit, KeyboardInterrupt):
        logger.info("KeyboardInterrupt")
        loop.run_until_complete(runner.shutdown_(logger, loop))
    except Exception as err:
        logger.exception(f"[1]Caught exception: {err}")
        loop.run_until_complete(runner.shutdown_(logger, loop))


ApplicationType = TypeVar("ApplicationType", bound=BaseApplication)
