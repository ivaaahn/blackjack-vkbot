import asyncio
from asyncio import Task
from typing import Optional

from app.config import setup_config, Config
from app.databases import setup_databases, Databases
from app.store import Store, setup_store, VkApiAccessor
from app.store.rabbit.accessor import RabbitAccessor

from app.app_logger import get_logger

logger = get_logger(__file__)


class Poller:
    def __init__(self, store: Store, databases: Databases, config: Config):
        self.store = store
        self.databases = databases
        self.config = config

        self.is_running = False
        self.poll_task: Optional[Task] = None

    @property
    def rabbit(self) -> RabbitAccessor:
        return self.store.rabbit

    @property
    def vk_api(self) -> VkApiAccessor:
        return self.store.vk_api

    async def start(self):
        logger.info('Poller starting ...')

        await self.databases.connect_for_poller()
        await self.store.connect_for_poller()

        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        logger.info('Poller stopping ...')
        await self.store.disconnect_for_poller()
        await self.databases.disconnect_for_poller()

        if self.poll_task and self.is_running:
            self.is_running = False
            self.poll_task.cancel()

        logger.info('Poller stopped')

    async def poll(self):
        logger.info('Poller started')

        while self.is_running:
            updates = await self.store.vk_api.poll()
            logger.info(f'Updates: {updates}')
            if updates:
                await self.rabbit.send_message(updates)


def setup_poller(config_path: str) -> Poller:
    config = setup_config(config_path)
    databases = setup_databases(config)
    store = setup_store(databases, config)
    return Poller(store, databases, config)


def run_poller(poller: Poller) -> None:
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(poller.start())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
    except Exception as e:
        logger.exception(f'Poller exception: {e}')
    finally:
        loop.run_until_complete(poller.stop())
        logger.info('Closing loop ...')
        loop.close()
        logger.info('Loop closed')
