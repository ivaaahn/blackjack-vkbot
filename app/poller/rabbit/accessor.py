from aio_pika import Channel, Message, DeliveryMode, Exchange
from app.poller.rabbit.rabbit import Rabbit


class RabbitAccessor:
    def __init__(self, rabbit: Rabbit) -> None:
        self.rabbit = rabbit

    @property
    def channel(self) -> Channel:
        return self.rabbit.channel

    @property
    def exchange(self) -> Exchange:
        return self.channel.default_exchange

    @property
    def queue_name(self) -> str:
        return self.rabbit.cfg.queue_name

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send_message(self, message_body: str) -> None:
        try:
            await self.exchange.publish(
                Message(
                    message_body.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=self.queue_name,
            )
        except Exception as e:
            print(e)
            print(e.args)
