from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as setup_aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from multidict import MultiDictProxy

from .api.admin.models import AdminModel
from .api.app.middlewares import setup_middlewares
from .api.app.routes import setup_routes
from .config import Config, setup_config
from .databases import Databases, setup_databases
from .store import setup_store, Store
from app.app_logger import get_logger

logger = get_logger(__file__)


class Application(AiohttpApplication):
    config: Optional[Config] = None
    store: Optional[Store] = None
    databases: Optional[Databases] = None


class Request(AiohttpRequest):
    admin: Optional[AdminModel] = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("json", {})

    @property
    def query_data(self) -> MultiDictProxy[str]:
        return self.request.get("querystring", {})


app = Application()


def setup_app(config_path: str) -> Application:
    app.config = setup_config(config_path)
    setup_routes(app)
    setup_aiohttp_session(app, EncryptedCookieStorage(app.config.session.key))
    setup_middlewares(app)
    setup_aiohttp_apispec(
        app, title="BlackJackBot", url="/docs/json", swagger_path="/docs"
    )
    app.databases = setup_databases(app.config)
    app.store = setup_store(app.databases, app.config)

    app.on_startup.append(app.databases.connect_aiohttp)
    app.on_startup.append(app.store.connect_aiohttp)
    app.on_cleanup.append(app.store.disconnect_aiohttp)
    app.on_cleanup.append(app.databases.disconnect_aiohttp)
    return app
