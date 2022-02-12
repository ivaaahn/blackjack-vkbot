import asyncio
from typing import Optional, Mapping, Type

from .base import AbstractPoller
from ..config import ConfigType
from ..store import PollerStore
from ..store.vk.accessor import VkAccessor
from ..store.vk.dataclasses import Message, Update


class VkPoller(AbstractPoller[VkAccessor]):
    class Meta:
        name = "vk_poller"

    def __init__(
        self,
        store: PollerStore,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = None,
    ) -> None:
        super().__init__(
            store, VkAccessor(store), name=name, config=config, config_type=config_type
        )

    async def _poll(self):
        await super()._poll()

        while self._is_running:
            if updates := await self.api.poll():
                self._logger.debug(f"Updates: {updates}")
                await self.store.rmq_sender.put(updates)
                #
                # upd = updates['updates'][0]
                # self.logger.debug(f'{upd}')
                #
                # msg = Update.from_dict(upd).object.message
                #
                # await self.api.send_message(Message(peer_id=msg.peer_id, text="Hello"))
