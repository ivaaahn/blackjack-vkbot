import asyncio
import json
from typing import Optional, Type, Mapping

from aio_pika import Message as RMQMessage, DeliveryMode, connect, Channel, Queue
from aio_pika.connection import ConnectionType

from proj.store import BaseStore
from proj.store.base.accessor import ConnectAccessor
from proj.store.rabbitmq.sender.config import ConfigType, RabbitMQSenderConfig

__all__ = ("RabbitMQSender",)


class RabbitMQSender(ConnectAccessor[BaseStore, ConfigType]):
    class Meta:
        name = "rmq_sender"

    def __init__(
        self,
        store: BaseStore,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = RabbitMQSenderConfig,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)

        self._connection: Optional[ConnectionType] = None
        self._channel: Optional[Channel] = None
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

                self._is_ready = True

                return
            except Exception as err:
                self.logger.error(
                    f"Cannot connect to rabbitmq ({self.config.host}, {self.config.port}): {err})"
                )
                await asyncio.sleep(self.config.reconnect_timeout)

    async def put(self, data: list[dict]):
        await self._channel.default_exchange.publish(
            routing_key=self.config.queue_name,
            message=RMQMessage(
                body=json.dumps(data).encode(),
            ),
        )

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()
