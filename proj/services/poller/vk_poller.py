from asyncio import CancelledError

from proj.services.poller.base import AbstractPoller
from proj.store import Store


class VkPoller(AbstractPoller[Store, None]):
    async def _poll(self):
        await super()._poll()

        try:
            while self._is_running:
                if updates := await self.store.vk._poll():
                    self._logger.debug(f"Updates: {updates}")
                    await self.store.rabbit.send_message(updates)
        except CancelledError as err:
            self._logger.info(f"Poller.{self._name}'s task was cancelled")
            # TODO
