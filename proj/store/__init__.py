import typing
from collections import Mapping

from proj.store.base import BaseStore

if typing.TYPE_CHECKING:
    from proj.api import ApiApplication
    from proj.poller import PollerApplication
    from proj.core import CoreApplication


class ApiStore(BaseStore):
    def __init__(self, app: "ApiApplication", config: Mapping) -> None:
        super().__init__(app, config)

        from proj.store.mongo import MongoAccessor
        from proj.api.admin import AdminAccessor
        from proj.api.players import PlayersAccessor
        from proj.api.game_settings import GameSettingsAccessor

        self.mongo = MongoAccessor(self)
        self.admin = AdminAccessor(self)
        self.players = PlayersAccessor(self)
        self.game_settings = GameSettingsAccessor(self)


class PollerStore(BaseStore):
    def __init__(self, app: "PollerApplication", config: Mapping) -> None:
        super().__init__(app, config)

        # from proj.store.vk.accessor import VkAccessor
        from proj.store.rabbitmq.sender import RabbitMQSender
        from proj.poller.vk_poller import VkPoller

        self.rmq_sender = RabbitMQSender(self)
        # self.vk = VkAccessor(self)
        self.vk_poller = VkPoller(self)


class CoreStore(BaseStore):
    def __init__(self, app: "CoreApplication", config: Mapping) -> None:
        super().__init__(app, config)

        from proj.store.vk.accessor import VkAccessor
        from proj.store.redis import RedisAccessor
        from proj.api.game_settings import GameSettingsAccessor
        from proj.api.players import PlayersAccessor
        from proj.core.worker import GameRequestReceiver
        from proj.core.accessors import (
            GameCtxAccessor,
            GameInteractionAccessor,
        )
        from proj.store.mongo import MongoAccessor

        self.mongo = MongoAccessor(self)

        self.redis = RedisAccessor(self)
        self.game_settings = GameSettingsAccessor(self)
        self.players = PlayersAccessor(self)
        self.vk = VkAccessor(self)

        self.game_ctx = GameCtxAccessor(self)
        self.game_interact = GameInteractionAccessor(self)

        self.rmq_worker = GameRequestReceiver(self)
