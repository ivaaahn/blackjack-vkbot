import base64
import typing
from hashlib import sha256
from typing import Optional

import bcrypt
from asyncpg import UniqueViolationError

from app.base.base_accessor import BaseAccessor
from app.admin.models import AdminModel
from app.admin.dataclasses import Admin

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        cfg = app.config.admin

        await self.create_admin(
            email=cfg.email,
            password=cfg.password
        )

    async def disconnect(self, app: "Application"):
        pass

    async def get_by_email(self, email: str) -> Optional[Admin]:
        admin_model: Optional[AdminModel] = await AdminModel.query.where(AdminModel.email == email).gino.first()
        if admin_model is not None:
            return Admin(id=admin_model.id, email=admin_model.email, password=admin_model.password)

        return None

    async def create_admin(self, email: str, password: str) -> Optional[Admin]:
        try:
            admin = await AdminModel.create(email=email, password=self._password_hasher(password))
        except UniqueViolationError:
            return None

        return admin

    @staticmethod
    def _password_hasher(raw_password: str) -> str:
        hash_binary = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())
        encoded = base64.b64encode(hash_binary)
        return encoded.decode('utf-8')
