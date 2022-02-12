from typing import Mapping, Iterable

from proj.base.application import BaseApplication, run_nonserver_app
from proj.store import PollerStore
from proj.store.base.accessor import ConnectAccessor
from .base import AbstractPoller
from .vk_poller import VkPoller

__all__ = (
    "PollerApplication",
    "run_poller",
    "create_app",
)

from ..logger import LoggerFactory


class PollerApplication(BaseApplication[PollerStore]):
    class Meta:
        name = "poller"

    def __init__(
        self,
        config: Mapping,
        logger_factory: "LoggerFactory",
        **kwargs,
    ) -> None:
        super().__init__(config, logger_factory, **kwargs)

    def make_poller(self) -> AbstractPoller:
        return VkPoller(self.store)

    def make_store(self) -> PollerStore:
        return PollerStore(self, config=self.config["store"])

    @property
    def accessors(self) -> Iterable[ConnectAccessor]:
        yield self.store.rmq_sender
        yield self.store.vk_poller


def create_app(config: Mapping, logger_factory: "LoggerFactory") -> PollerApplication:
    return PollerApplication(config, logger_factory)


def run_poller(app: PollerApplication) -> None:
    run_nonserver_app(app)
