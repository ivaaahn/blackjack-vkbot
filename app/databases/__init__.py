from typing import TYPE_CHECKING

from app.config import Config

from .mongo import Mongo
from .rabbit import Rabbit
from .redis import Redis

if TYPE_CHECKING:
    from app.app import Application


class Databases:
    def __init__(self, config: Config) -> None:
        self.redis = Redis(config)
        self.mongo = Mongo(config)
        self.rabbit = Rabbit(config)

    async def connect_for_poller(self) -> None:
        await self.rabbit.connect()

    async def connect_for_worker(self) -> None:
        await self.rabbit.connect()
        await self.redis.connect()
        await self.mongo.connect()

    async def disconnect_for_poller(self) -> None:
        await self.rabbit.disconnect()

    async def disconnect_for_worker(self) -> None:
        await self.rabbit.disconnect()
        await self.redis.disconnect()
        await self.mongo.disconnect()

    async def connect_aiohttp(self, _: 'Application') -> None:
        await self.mongo.connect()

    async def disconnect_aiohttp(self, _: 'Application') -> None:
        await self.mongo.disconnect()


def setup_databases(config: Config) -> Databases:
    return Databases(config)
