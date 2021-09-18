from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from motor.motor_asyncio import AsyncIOMotorClient

from app.base.base_database import BaseDatabase

if TYPE_CHECKING:
    from app.app import Application
    from motor.motor_asyncio import (AsyncIOMotorDatabase,
                                     AsyncIOMotorCollection)


@dataclass
class Collections:
    players: Optional['AsyncIOMotorCollection'] = None
    admins: Optional['AsyncIOMotorCollection'] = None
    game_settings: Optional['AsyncIOMotorCollection'] = None


class Mongo(BaseDatabase):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.collects: Optional[Collections] = None

    async def connect(self, app: "Application") -> None:
        cfg = app.config.mongo

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

    async def disconnect(self, app: "Application") -> None:
        pass


def setup_mongo(app: "Application") -> None:
    app.mongo = Mongo(app)
