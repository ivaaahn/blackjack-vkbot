import logging
import typing
import weakref
from collections import Mapping
from typing import Generic, Optional, TypeVar

if typing.TYPE_CHECKING:
    from proj.store.base.accessor import Accessor

__all__ = (
    "BaseStore",
    "S",
)


class BaseStore:
    __frozen__ = False

    class Meta:
        name = None

    def __init__(self, app, config: Mapping, *, name: Optional[str] = None):
        self._app = weakref.ref(app)
        self._name = name or self.Meta.name or self.__class__.__name__
        self._logger = app.get_logger(f"Store.{self._name}")
        self._config = config or {}
        self._accessors: dict[str, "Accessor"] = {}

    @property
    def app(self):
        return self._app()

    # def __freeze__(self):
    #     self.__frozen__ = True

    @property
    def config(self) -> Mapping:
        return self._config

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def accessors(self) -> Mapping[str, "Accessor"]:
        return self._accessors

    # def __getattribute__(self, item):
    #     try:
    #         return super().__getattribute__(item)
    #     except AttributeError:
    #         if item in self._accessors:
    #             return self._accessors[item]
    #         raise AttributeError(f"Accessor {item} not found")
    #
    # def __setattr__(self, key, value):
    #     if self.__frozen__ and not hasattr(self, key):
    #         if not isinstance(value, Accessor):
    #             raise ValueError(
    #                 f"Cannot set non-Accessor to store. Got: {repr(value)}"
    #             )
    #
    #         self._accessors[key] = value
    #         if not value._name_is_custom:
    #             value._name = key
    #         return
    #
    #     return object.__setattr__(self, key, value)


S = TypeVar("S", bound=BaseStore)
