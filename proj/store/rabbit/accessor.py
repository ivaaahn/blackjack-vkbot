import asyncio
from typing import Optional, Mapping, Type

from aio_pika import connect, Channel, Exchange, Queue
from aio_pika.connection import ConnectionType

from proj.store import Store
from proj.store.base.accessor import ConnectAccessor
from proj.store.rabbit.config import ConfigType, RabbitConfig

__all__ = ('RabbitAccessor')


class RabbitAccessor(ConnectAccessor[Store, ConfigType]):
    class Meta:
        name = "rabbit"

    def __init__(
        self,
        store: Store,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = RabbitConfig,
    ):
        super().__init__(
            store, name=name, config=config, config_type=config_type
        )

        self._connection: Optional[ConnectionType] = None
        self._channel: Optional[Channel] = None
        self._exchange: Optional[Exchange] = None
        self._queue: Optional[Queue] = None

    async def _connect(self) -> None:
        while True:
            try:
                self._connection = await connect(
                    host=self.config.host,
                    port=self.config.port,
                    login=self.config.user,
                    password=self.config.password,
                )

                self._channel = await self._connection.channel()
                self._queue = await self._channel.declare_queue(
                    self.config.queue_name, durable=True
                )

                return
            except Exception as err:
                self.logger.error(
                    f"Cannot connect to rabbit ({self.config.host}, {self.config.port}): {err})"
                )
                await asyncio.sleep(self.config.reconnect_timeout)

    async def disconnect(self) -> None:
        await self._connection.close()

    async def register_consumer(self, func):
        await self._queue.consume(func)
        self.logger.info("Consumer registered")
