import asyncio
from asyncio import Task
from typing import Optional

from app.store import Store
from app.store.rabbit.accessor import RabbitAccessor


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None

    @property
    def rabbit(self) -> RabbitAccessor:
        return self.store.rabbit

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        if self.poll_task and self.is_running:
            self.is_running = False
            self.poll_task.cancel()

    async def poll(self):
        while self.is_running:
            if updates := await self.store.vk_api.poll():
                await self.rabbit.send_message(updates)

