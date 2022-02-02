import asyncio
from collections import Mapping
from typing import Optional

from proj.store.base.store import BaseStore


class Store(BaseStore):
    def __init__(
        self,
        config: Mapping,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(config, loop=loop)

        from proj.store.mongo import MongoAccessor
        from proj.store.redis import RedisAccessor
        from proj.store.rabbit import RabbitAccessor

        self.mongo = MongoAccessor(self)
        self.redis = RedisAccessor(self)
        self.rabbit = RabbitAccessor(self)