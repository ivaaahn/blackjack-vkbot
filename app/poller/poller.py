import asyncio
import traceback
from asyncio import Task
from signal import SIGINT, SIGTERM
from typing import Optional

from .config import setup_config, Config
from .rabbit.rabbit import Rabbit
from .rabbit.accessor import RabbitAccessor
# from vk.vk_api.accessor import VkApiAccessor
from .vk import VkApiAccessor


class Poller:
    def __init__(self, rabbit: RabbitAccessor, vk_api: VkApiAccessor):
        self.rabbit = rabbit
        self.vk_api = vk_api
        self.is_running = False
        self.poll_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        await asyncio.gather(self.poll_task)

    async def stop(self):
        if self.poll_task and self.is_running:
            self.is_running = False
            self.poll_task.cancel()

    async def poll(self):
        while self.is_running:
            if updates := await self.vk_api.poll():
                await self.rabbit.send_message(updates)


async def _setup(config: Config):
    vk_api_accessor = VkApiAccessor(config.bot)
    await vk_api_accessor.connect()

    rabbit = Rabbit(cfg=config.rabbit)
    await rabbit.connect()

    rabbit_accessor = RabbitAccessor(rabbit)
    await rabbit_accessor.connect()

    poller = Poller(rabbit_accessor, vk_api_accessor)

    await poller.start()


def run_poller(config_path: str):
    loop = asyncio.get_event_loop()
    # task = asyncio.create_task(_run (setup_config(config_path)))

    try:
        loop.run_until_complete(asyncio.gather(_setup(setup_config(config_path))))
    except KeyboardInterrupt:
        print("GG")
    except Exception as e:
        print(e)
        traceback.print_exc()
