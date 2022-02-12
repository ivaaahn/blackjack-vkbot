import typing
from typing import Optional, Generic

from aiohttp.web import (
    View as AiohttpView,
    Request as AiohttpRequest,
)
from multidict import MultiDictProxy

from proj.store.base import S
from ..admin.models import AdminModel
from ..application import ApiApplication

from ...base.application import ApplicationType
from proj.store import ApiStore


class Request(AiohttpRequest):
    admin: Optional[AdminModel] = None

    @property
    def app(self) -> ApiApplication:
        return super().app


class BaseView(Generic[ApplicationType, S], AiohttpView):
    def __init__(self, request: Request):
        super().__init__(request)
        self._app = self.request.app

    @property
    def app(self) -> ApplicationType:
        return self._app

    @property
    def store(self) -> S:
        return self.app.store

    @property
    def request(self) -> Request:
        return super().request

    @property
    def body(self) -> dict:
        return self.request.get("json", {})

    @property
    def query_string(self) -> MultiDictProxy[str]:
        return self.request.get("querystring", {})


class View(BaseView[ApiApplication, ApiStore]):
    pass
