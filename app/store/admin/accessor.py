import typing
from typing import Optional
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from app.admin.models import AdminModel
from app.base.base_accessor import BaseAccessor
from app.admin.utils import hash_pwd

if typing.TYPE_CHECKING:
    from app.web.app import Application
    from motor.motor_asyncio import AsyncIOMotorCollection


class AdminAccessor(BaseAccessor):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)

    @property
    def collect(self) -> "AsyncIOMotorCollection":
        return self.app.mongo.collects.admins

    @property
    def cfg(self):
        return self.app.config.admin

    async def connect(self, app: "Application"):
        await self.create_admin(
            email=self.cfg.email,
            password=self.cfg.password
        )

    async def disconnect(self, app: "Application"):
        pass

    async def get_by_email(self, email: str) -> Optional[AdminModel]:
        raw_admin = await self.collect.find_one({'email': email})

        if raw_admin is not None:
            return AdminModel.from_dict(raw_admin)

        return None

    async def create_admin(self, email: str, password: str):
        model = AdminModel(_id=uuid4(), email=email, password=hash_pwd(password))

        try:
            await self.collect.insert_one(model.to_dict())
        except DuplicateKeyError:
            pass
