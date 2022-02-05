from typing import Mapping, Iterable

from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as setup_aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from proj.store import Store
from proj.store.base.accessor import ConnectAccessor

from proj.base.app import BaseApplication
from .web.middlewares import setup_middlewares
from .web.urls import setup_routes

__all__ = (
    "ApiApplication",
    "create_app",
)


class ApiApplication(BaseApplication):
    class Meta:
        name = "api"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        setup_routes(self)
        setup_aiohttp_session(
            self, EncryptedCookieStorage(self.config["session"]["key"])
        )
        setup_middlewares(self)
        setup_aiohttp_apispec(
            self, title="BlackJackBot", url="/docs/json", swagger_path="/docs"
        )

    def make_store(self) -> Store:
        return Store(config=self.config.get("store"))

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        yield self.store.mongo
        yield self.store.admin
        yield self.store.players


def create_app(config: Mapping) -> ApiApplication:
    return ApiApplication(config)
