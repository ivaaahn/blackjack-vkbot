from typing import Optional, TYPE_CHECKING

from aio_pika import connect, Channel, Exchange, Queue
from aio_pika.connection import ConnectionType

from app.base.base_database import BaseDatabase

if TYPE_CHECKING:
    from app.app import Application


class Rabbit(BaseDatabase):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)
        self.conn: Optional[ConnectionType] = None
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None
        self.queue: Optional[Queue] = None

    async def connect(self, app: "Application") -> None:
        cfg = app.config.rabbit

        self.conn = await connect(
            host=cfg.host,
            port=cfg.port,
            login=cfg.user,
            password=cfg.password,
            loop=app._loop,  # TODO (Where should I take the loop?)
        )

        self.channel = await self.conn.channel()
        self.queue = await self.channel.declare_queue(cfg.queue_name, durable=True)

    async def disconnect(self, app: "Application") -> None:
        await self.conn.close()  # TODO When should I do it?

    async def register_consumer(self):
        await self.queue.consume(self.app.bot_manager.handle_updates)


def setup_rabbit(app: "Application") -> None:
    app.rabbit = Rabbit(app)
