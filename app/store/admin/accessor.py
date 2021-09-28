from typing import Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError

from app.api.admin.models import AdminModel
from app.api.admin.utils import hash_pwd
from app.base.mongo_accessor import MongoAccessor
from app.config import Config, AdminConfig
from app.databases import Databases
from app.app_logger import get_logger

logger = get_logger(__file__)


class AdminAccessor(MongoAccessor):
    def __init__(self, databases: Databases, config: Config) -> None:
        super().__init__(databases, config)

    @property
    def coll(self) -> AsyncIOMotorCollection:
        return self.mongo.collects.admins

    @property
    def cfg(self) -> AdminConfig:
        return self.config.admin

    async def connect(self) -> None:
        await self.create_admin(
            email=self.cfg.email,
            password=self.cfg.password
        )

        logger.info('Admin accessor connected')

    async def get_by_email(self, email: str) -> Optional[AdminModel]:
        raw_admin = await self.coll.find_one({'email': email})

        if raw_admin is not None:
            return AdminModel.from_dict(raw_admin)

        return None

    async def create_admin(self, email: str, password: str):
        model = AdminModel(_id=uuid4(), email=email, password=hash_pwd(password))

        try:
            await self.coll.insert_one(model.to_dict())
        except DuplicateKeyError:
            pass
