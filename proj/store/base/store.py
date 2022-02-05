import asyncio
import logging
from collections import Mapping

from proj.store.base.accessor import Accessor


class BaseStore:
    __frozen__ = False

    def __init__(
        self,
        config: Mapping,
    ):
        self._logger = logging.getLogger("store")
        self._config = self.check_config(config) or {}
        self._accessors: dict[str, Accessor] = {}

    def __freeze__(self):
        self.__frozen__ = True

    def check_config(self, config: Mapping) -> Mapping:
        return config

    @property
    def config(self) -> Mapping:
        return self._config

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    @property
    def accessors(self) -> Mapping[str, Accessor]:
        return self._accessors

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            if item in self._accessors:
                return self._accessors[item]
            raise AttributeError(f"Accessor {item} not found")

    def __setattr__(self, key, value):
        if self.__frozen__ and not hasattr(self, key):
            if not isinstance(value, Accessor):
                raise ValueError(
                    f"Cannot set non-Accessor to store. Got: {repr(value)}"
                )

            self._accessors[key] = value
            if not value._name_is_custom:
                value._name = key
            return

        return object.__setattr__(self, key, value)
