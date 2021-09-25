import typing

from aio_pika import Channel, Message, DeliveryMode, Exchange

from app.base.base_accessor import BaseAccessor
from app.config import RabbitConfig

if typing.TYPE_CHECKING:
    from app.app import Application


class RabbitAccessor(BaseAccessor):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)

    @property
    def channel(self) -> Channel:
        return self.app.rabbit.channel

    @property
    def exchange(self) -> Exchange:
        return self.app.rabbit.channel.default_exchange

    @property
    def cfg(self) -> RabbitConfig:
        return self.app.config.rabbit

    async def connect(self, app: "Application") -> None:
        await self.app.rabbit.register_consumer()  # TODO

    async def disconnect(self, app: "Application") -> None:
        pass

    async def send_message(self, message_body: str) -> None:
        try:
            await self.exchange.publish(
                Message(
                    message_body.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=self.cfg.queue_name,
            )
        except Exception as e:
            print(e)
            print(e.args)
