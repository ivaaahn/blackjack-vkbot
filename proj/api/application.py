from typing import Mapping, Iterable

from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as setup_aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from proj.store.base.accessor import ConnectAccessor

from proj.base.application import BaseApplication
from .web.middlewares import setup_middlewares
from .web.urls import setup_routes as setup_api_routes

__all__ = (
    "ApiApplication",
    "create_app",
)

from proj.store import ApiStore
from ..logger import LoggerFactory


class ApiApplication(BaseApplication):
    class Meta:
        name = "api"

    def __init__(
        self, config: Mapping, logger_factory: LoggerFactory, **kwargs
    ) -> None:
        super().__init__(config, logger_factory, **kwargs)

        setup_api_routes(self)
        setup_aiohttp_session(
            self, EncryptedCookieStorage(self.config["session"]["key"])
        )
        setup_middlewares(self)
        setup_aiohttp_apispec(
            self, title="BlackJackBot", url="/docs/json", swagger_path="/docs"
        )

    def make_store(self) -> ApiStore:
        return ApiStore(self, config=self.config.get("store"))

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        yield self.store.mongo
        yield self.store.admin
        yield self.store.players


def create_app(config: Mapping, logger_factory: LoggerFactory) -> ApiApplication:
    return ApiApplication(config, logger_factory)
