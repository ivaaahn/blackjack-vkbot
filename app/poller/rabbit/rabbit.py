from typing import Optional

from aio_pika import connect, Channel, Exchange, Queue
from aio_pika.connection import ConnectionType

from app.poller.config import RabbitConfig


class Rabbit:
    def __init__(self, cfg: RabbitConfig) -> None:
        self.conn: Optional[ConnectionType] = None
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None
        self.queue: Optional[Queue] = None
        self.cfg = cfg

    async def connect(self) -> None:
        cfg = self.cfg

        # print(self.cfg)

        self.conn = await connect(
            host=cfg.host,
            port=cfg.port,
            login=cfg.user,
            password=cfg.password,
            # loop=loop,
        )

        self.channel = await self.conn.channel()
        self.queue = await self.channel.declare_queue(cfg.queue_name, durable=True)

    async def disconnect(self) -> None:
        await self.conn.close()
