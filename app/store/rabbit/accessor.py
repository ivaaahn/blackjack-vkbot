from aio_pika import Channel, Message, DeliveryMode, Exchange

from app.base.base_accessor import BaseAccessor
from app.config import RabbitConfig, Config
from app.databases import Databases
from app.databases.rabbit import Rabbit
from app.app_logger import get_logger

logger = get_logger(__file__)


class RabbitAccessor(BaseAccessor):
    def __init__(self, databases: Databases, config: Config) -> None:
        super().__init__(databases, config)

    @property
    def rabbit(self) -> Rabbit:
        return self.databases.rabbit

    @property
    def queue_name(self) -> str:
        return self.cfg.queue_name

    @property
    def channel(self) -> Channel:
        return self.rabbit.channel

    @property
    def exchange(self) -> Exchange:
        return self.rabbit.channel.default_exchange

    @property
    def cfg(self) -> RabbitConfig:
        return self.config.rabbit

    async def connect(self) -> None:
        logger.info('Rabbit accessor connected')

    async def disconnect(self) -> None:
        logger.info('Rabbit accessor disconnected')

    async def send_message(self, message_body: str) -> None:
        try:
            await self.exchange.publish(
                Message(
                    message_body.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=self.queue_name
            )
        except Exception as e:
            logger.exception(f'Exception during send message to queue: {e}')
