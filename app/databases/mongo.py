from dataclasses import dataclass
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from app.base.base_database import BaseDatabase
from app.config import Config, MongoConfig

from app.app_logger import get_logger

logger = get_logger(__file__)


@dataclass
class Collections:
    players: Optional[AsyncIOMotorCollection] = None
    admins: Optional[AsyncIOMotorCollection] = None
    game_settings: Optional[AsyncIOMotorCollection] = None


class Mongo(BaseDatabase):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.collects: Optional[Collections] = None

    @property
    def cfg(self) -> MongoConfig:
        return self.config.mongo

    async def connect(self) -> None:
        logger.info('Mongo connected')

        cfg = self.cfg

        self.client = AsyncIOMotorClient(
            host=cfg.host,
            port=cfg.port,
            username=cfg.user,
            password=cfg.password,
            uuidRepresentation=cfg.uuidRepresentation
        )

        self.db = self.client[cfg.db]
        self.collects = Collections(
            players=self.db[cfg.collections.players],
            admins=self.db[cfg.collections.admins],
            game_settings=self.db[cfg.collections.game_settings]
        )

    async def disconnect(self) -> None:
        logger.info('Mongo disconnected')


def setup_mongo(config: Config) -> Mongo:
    return Mongo(config)
