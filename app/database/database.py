import typing
from dataclasses import dataclass, field

import gino
from gino import Gino

from app.admin.dataclasses import Admin
from app.base.base_database import BaseDatabase
from sqlalchemy.engine.url import URL

# from .gino import gino_db
from app.database.gino import db

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Database(BaseDatabase):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)
        self.db = db

    async def connect(self, app: "Application") -> None:
        print("Database.connect()")

        cfg = app.config.database

        self.db.bind = await gino.create_engine(
            URL(
                drivername="asyncpg",
                host=cfg.host,
                port=cfg.port,
                username=cfg.user,
                password=cfg.password,
                database=cfg.database,
            ),
            min_size=1,
            max_size=1,
        )

    async def disconnect(self, app: "Application") -> None:
        print("Database.disconnect()")
        await self.db.pop_bind().close()


def setup_database(app: "Application") -> None:
    app.database = Database(app)
