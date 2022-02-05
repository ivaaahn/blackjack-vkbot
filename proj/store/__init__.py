from collections import Mapping

from proj.store.base.store import BaseStore


class Store(BaseStore):
    def __init__(
        self,
        config: Mapping,
    ):
        super().__init__(config)

        from proj.store.mongo import MongoAccessor
        from proj.store.redis import RedisAccessor
        from proj.store.rabbit import RabbitAccessor
        from proj.store.vk.accessor import VkAccessor

        from proj.services.api.admin import AdminAccessor
        from proj.services.api.game_settings import GameSettingsAccessor
        from proj.services.api.players import PlayersAccessor

        from proj.core.accessors import (
            GameCtxAccessor,
            GameInteractionAccessor,
        )

        self.mongo = MongoAccessor(self)
        self.redis = RedisAccessor(self)
        self.rabbit = RabbitAccessor(self)

        self.admin = AdminAccessor(self)
        self.game_settings = GameSettingsAccessor(self)
        self.players = PlayersAccessor(self)
        self.vk = VkAccessor(self)

        self.game_ctx = GameCtxAccessor(self)
        self.game_interact = GameInteractionAccessor(self)
