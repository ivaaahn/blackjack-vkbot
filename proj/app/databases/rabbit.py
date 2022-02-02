from typing import Optional

from aio_pika import connect, Channel, Exchange, Queue
from aio_pika.connection import ConnectionType

from app.base.base_database import BaseDatabase
from app.config import Config, RabbitConfig

from app.app_logger import get_logger

logger = get_logger(__file__)


class Rabbit(BaseDatabase):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.conn: Optional[ConnectionType] = None
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None
        self.queue: Optional[Queue] = None

    @property
    def cfg(self) -> RabbitConfig:
        return self.config.rabbit

    async def connect(self) -> None:
        logger.info("Rabbitmq connected")
        cfg = self.cfg

        self.conn = await connect(
            host=cfg.host,
            port=cfg.port,
            login=cfg.user,
            password=cfg.password,
        )

        self.channel = await self.conn.channel()
        self.queue = await self.channel.declare_queue(cfg.queue_name, durable=True)

    async def disconnect(self) -> None:
        logger.info("Rabbitmq disconnected")
        await self.conn.close()

    async def register_consumer(self, func):
        logger.info("Consumer registered")
        await self.queue.consume(func)


def setup_rabbit(config: Config) -> Rabbit:
    return Rabbit(config)
