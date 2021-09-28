from typing import TYPE_CHECKING

from app.config import Config
from app.databases import Databases

from .players.accessor import PlayersAccessor
from .vk_api.accessor import VkApiAccessor
from .admin.accessor import AdminAccessor
from .game.redis_accessor import RedisGameAccessor
from .game_settings.accessor import GameSettingsAccessor
from .rabbit.accessor import RabbitAccessor

if TYPE_CHECKING:
    from app.app import Application


class Store:
    def __init__(self, dbs: Databases, config: Config):
        self.game_settings = GameSettingsAccessor(dbs, config)
        self.admins = AdminAccessor(dbs, config)
        self.vk_api = VkApiAccessor(dbs, config)
        self.players = PlayersAccessor(dbs, config)
        self.game = RedisGameAccessor(dbs, config)
        self.rabbit = RabbitAccessor(dbs, config)

    @property
    def poller_accessors(self) -> tuple:
        return self.rabbit, self.vk_api

    @property
    def bot_accessors(self) -> tuple:
        return self.rabbit, self.vk_api, self.game, self.game_settings, self.players

    @property
    def api_accessors(self) -> tuple:
        return self.admins, self.players

    async def connect_for_poller(self) -> None:
        for accessor in self.poller_accessors:
            await accessor.connect()

    async def connect_for_worker(self) -> None:
        for accessor in self.bot_accessors:
            await accessor.connect()

    async def disconnect_for_poller(self) -> None:
        for accessor in self.poller_accessors:
            await accessor.disconnect()

    async def disconnect_for_worker(self) -> None:
        for accessor in self.bot_accessors:
            await accessor.disconnect()

    async def connect_aiohttp(self, _: 'Application') -> None:
        for accessor in self.api_accessors:
            await accessor.connect()

    async def disconnect_aiohttp(self, _: 'Application') -> None:
        for accessor in self.api_accessors:
            await accessor.disconnect()


def setup_store(databases: Databases, config: Config) -> Store:
    return Store(databases, config)
