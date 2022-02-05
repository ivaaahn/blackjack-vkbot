import asyncio
from dataclasses import dataclass
from typing import Optional, Mapping, Type

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
)

from proj.store import Store
from proj.store.base.accessor import ConnectAccessor
from proj.store.mongo.config import ConfigType, MongoConfig, MongoCollectionsConfig

__all__ = (
    "MongoCollections",
    "MongoAccessor",
)


@dataclass
class MongoCollections:
    players: Optional[AsyncIOMotorCollection] = None
    admins: Optional[AsyncIOMotorCollection] = None
    game_settings: Optional[AsyncIOMotorCollection] = None


class MongoAccessor(ConnectAccessor[Store, ConfigType]):
    class Meta:
        name = "mongo"

    def __init__(
        self,
        store: Store,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = MongoConfig,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)
        self.config.collections = MongoCollectionsConfig(**self.config.collections)

        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._collections: Optional[MongoCollections] = None

    @property
    def admins_coll(self) -> AsyncIOMotorCollection:
        return self._collections.admins

    @property
    def players_coll(self) -> AsyncIOMotorCollection:
        return self._collections.players

    @property
    def game_settings_coll(self) -> AsyncIOMotorCollection:
        return self._collections.game_settings

    async def _connect(self) -> None:
        while True:
            self._client = AsyncIOMotorClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.user,
                password=self.config.password,
                uuidRepresentation=self.config.uuidRepresentation,
                serverSelectionTimeoutMS=self.config.server_selection_timeout,
            )

            self._db = self._client[self.config.db]
            self._collections = MongoCollections(
                players=self._db[self.config.collections.players],
                admins=self._db[self.config.collections.admins],
                game_settings=self._db[self.config.collections.game_settings],
            )

            try:
                await self._client.server_info()
                return
            except Exception as err:
                self.logger.error(
                    f"Cannot connect to mongo ({self.config.host}, {self.config.port}): {err})"
                )
                await asyncio.sleep(self.config.reconnect_timeout)

    async def _disconnect(self):
        pass
