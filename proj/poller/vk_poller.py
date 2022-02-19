import asyncio
from typing import Optional, Mapping, Type, Tuple
from pprint import pformat

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

    @staticmethod
    def _extract_updates(updates: dict) -> tuple[Optional[str], list[dict]]:
        if not updates:
            return None, []

        return updates.get("ts", None), updates.get("updates", [])

    async def _poll(self):
        await super()._poll()

        while self._is_running:
            if not (updates := await self.api.poll()):
                continue

            ts, updates = self._extract_updates(updates)

            if updates:
                self.logger.debug(f"{ts=}, {updates=}")
                await self.store.rmq_sender.put(updates)
