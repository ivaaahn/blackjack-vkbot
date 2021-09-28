from motor.motor_asyncio import AsyncIOMotorCollection

from app.base.base_accessor import BaseAccessor
from app.config import Config
from app.databases import Databases, Mongo


class MongoAccessor(BaseAccessor):
    def __init__(self, databases: Databases, config: Config) -> None:
        super().__init__(databases, config)

    @property
    def mongo(self) -> Mongo:
        return self.databases.mongo

    @property
    def coll(self) -> AsyncIOMotorCollection:
        raise NotImplemented

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass
