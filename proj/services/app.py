# from typing import Optional
#
# from aiohttp.web import (
#     Application as AiohttpApplication,
#     View as AiohttpView,
#     Request as AiohttpRequest,
# )
# from aiohttp_apispec import setup_aiohttp_apispec
# from aiohttp_session import setup as setup_aiohttp_session
# from aiohttp_session.cookie_storage import EncryptedCookieStorage
# from multidict import MultiDictProxy
#
# from .api.admin.models import AdminModel
# from .api.services.middlewares import setup_middlewares
# from .api.services.routes import setup_routes
# from .config import Config, setup_config
# from .databases import Databases, setup_databases
# from .store import setup_store, Store
# from services.app_logger import get_logger
#
# logger = get_logger(__file__)
#
#
# class Application(AiohttpApplication):
#     config: Optional[Config] = None
#     store: Optional[Store] = None
#     databases: Optional[Databases] = None
#
#
# class Request(AiohttpRequest):
#     admin: Optional[AdminModel] = None
#
#     @property
#     def services(self) -> Application:
#         return super().services()
#
#
# class View(AiohttpView):
#     @property
#     def request(self) -> Request:
#         return super().request
#
#     @property
#     def store(self) -> Store:
#         return self.request.services.store
#
#     @property
#     def data(self) -> dict:
#         return self.request.get("json", {})
#
#     @property
#     def query_data(self) -> MultiDictProxy[str]:
#         return self.request.get("querystring", {})
#
#
# services = Application()
#
#
# def setup_app(config_path: str) -> Application:
#     services.config = setup_config(config_path)
#     setup_routes(services)
#     setup_aiohttp_session(services, EncryptedCookieStorage(services.config.session.key))
#     setup_middlewares(services)
#     setup_aiohttp_apispec(
#         services, title="BlackJackBot", url="/docs/json", swagger_path="/docs"
#     )
#     services.databases = setup_databases(services.config)
#     services.store = setup_store(services.databases, services.config)
#
#     services.on_startup.append(services.databases.connect_aiohttp)
#     services.on_startup.append(services.store.connect_aiohttp)
#
#     services.on_cleanup.append(services.store.disconnect_aiohttp)
#     services.on_cleanup.append(services.databases.disconnect_aiohttp)
#     return services
