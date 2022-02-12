import asyncio
import traceback
from typing import Optional, Type, Mapping

from aio_pika import connect, Channel, Queue, IncomingMessage
from aio_pika.connection import ConnectionType

from proj.store import BaseStore, CoreStore
from proj.store.base.accessor import ConnectAccessor
from proj.store.rabbitmq.worker.config import ConfigType, RabbitMQWorkerConfig


class RabbitMQWorker(ConnectAccessor[CoreStore, ConfigType]):
    class Meta:
        name = "rmq_worker"

    def __init__(
        self,
        store: CoreStore,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = RabbitMQWorkerConfig,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)

        self._is_ready = False
        self._is_running = False

        self._connection: Optional[ConnectionType] = None
        self._channel: Optional[Channel] = None
        self._queue: Optional[Queue] = None

        self._concurrent_workers = 0
        self._stop_event = asyncio.Event()
        self._consume_tag: Optional[str] = None

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
                await self._channel.set_qos(prefetch_count=self.config.capacity)

                self._queue = await self._channel.declare_queue(
                    self.config.queue_name, durable=True
                )

                self._is_running = True
                self._consume_tag = await self._queue.consume(self._worker)
                self.logger.info("RMQ WORKER CONNECTED")
                return
            except Exception as err:
                self.logger.error(
                    f"Cannot connect to rabbitmq ({self.config.host}, {self.config.port}): {err})"
                )
                await asyncio.sleep(self.config.reconnect_timeout)

    async def handler(self, msg: IncomingMessage):
        print(msg)

    async def _worker(self, msg: IncomingMessage):
        async with msg.process():
            self._concurrent_workers += 1
            try:
                await self.handler(msg)
            except Exception:
                traceback.print_exc()
            finally:
                self._concurrent_workers -= 1
                if not self._is_running and self._concurrent_workers == 0:
                    self._stop_event.set()

    async def _disconnect(self):
        if self._consume_tag:
            await self._queue.cancel(self._consume_tag)
        self._is_running = False
        if self._concurrent_workers != 0:
            self._stop_event = asyncio.Event()
            await self._stop_event.wait()
        await self._connection.close()
