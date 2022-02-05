from typing import Optional, Mapping, Type
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from proj.store import Store
from proj.store.base.accessor import ConnectAccessor
from .config import ConfigType, AdminConfig
from .models import AdminModel
from .utils import hash_pwd

__all__ = ("AdminAccessor",)


class AdminAccessor(ConnectAccessor[Store, ConfigType]):
    class Meta:
        name = "admin"

    def __init__(
        self,
        store: Store,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = AdminConfig,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)

    async def _connect(self) -> None:
        await self._create_admin(
            email=self.config.email,
            password=self.config.password,
        )

    async def get_by_email(self, email: str) -> Optional[AdminModel]:
        raw_admin = await self.store.mongo.admins_coll.find_one({"email": email})
        return AdminModel.from_dict(raw_admin) if raw_admin else None

    async def _create_admin(self, email: str, password: str):
        model = AdminModel(
            _id=uuid4(),
            email=email,
            password=hash_pwd(password),
        )

        try:
            await self.store.mongo.admins_coll.insert_one(model.to_dict())
        except DuplicateKeyError:
            pass
