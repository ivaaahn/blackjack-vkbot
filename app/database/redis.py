from typing import Optional, TYPE_CHECKING

from aioredis import from_url, client

from app.base.base_database import BaseDatabase

if TYPE_CHECKING:
    from app.web.app import Application


class Redis(BaseDatabase):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)
        self.client: Optional[client.Redis] = None

    async def connect(self, app: "Application") -> None:
        print("Redis.connect()")

        cfg = app.config.redis

        self.client = from_url(
            url=f'redis://{cfg.host}',
            # port=cfg.port,
            # username=cfg.user,
            # password=cfg.password,
            db=cfg.db,
            decode_responses=True,
        )

    async def disconnect(self, app: "Application") -> None:
        print("Redis.disconnect()")

        await self.client.close()


def setup_redis(app: "Application") -> None:
    app.redis = Redis(app)
