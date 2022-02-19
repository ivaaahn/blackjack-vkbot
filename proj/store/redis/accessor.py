import asyncio
from typing import Optional, Mapping, Type

from aioredis import from_url, client

from proj.store import CoreStore
from proj.store.base.accessor import ConnectAccessor
from proj.store.redis.config import ConfigType, RedisConfig

__all__ = ("RedisAccessor",)


class RedisAccessor(ConnectAccessor[CoreStore, ConfigType]):
    class Meta:
        name = "redis"

    def __init__(
        self,
        store: CoreStore,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = RedisConfig,
    ) -> None:
        super().__init__(store, name=name, config=config, config_type=config_type)

        self._client: Optional[client.Redis] = None

    async def _connect(self) -> None:
        while True:
            self._client = from_url(
                url=f"redis://{self.config.host}",
                port=self.config.port,
                # username=cfg.user,
                # password=self.config.password,
                db=self.config.db,
                decode_responses=True,
                encoding="utf-8",
            )

            try:
                print(await self._client.ping())  # TODO
                return
            except Exception as err:
                self.logger.error(
                    f"Cannot connect to redis ({self.config.host}, {self.config.port}): {err})"
                )
                await asyncio.sleep(self.config.reconnect_timeout)

    async def _disconnect(self) -> None:
        pass

    @property
    def client(self) -> client.Redis:
        return self._client
