from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.api.admin.models import AdminModel
from app.database.mongo import Mongo, setup_mongo
from app.database.redis import Redis, setup_redis
from app.store import setup_store, Store
from .config import Config, setup_config
from .logger import setup_logging
from .api.app.middlewares import setup_middlewares
from .api.app.routes import setup_routes
from aiohttp_session import setup as setup_aiohttp_session
from app.bot.manager import setup as setup_bot_manager, BotManager


class Application(AiohttpApplication):
    config: Optional[Config] = None
    store: Optional[Store] = None
    mongo: Optional[Mongo] = None
    redis: Optional[Redis] = None
    bot_manager: Optional[BotManager] = None


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
        return self.request.get("data", {})


app = Application()


def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    setup_routes(app)
    setup_aiohttp_session(app, EncryptedCookieStorage(app.config.session.key))
    setup_middlewares(app)
    setup_aiohttp_apispec(app, title='BlackJackBot', url='/docs/json', swagger_path='/docs')
    setup_redis(app)
    setup_mongo(app)
    setup_store(app)
    setup_bot_manager(app)
    return app
