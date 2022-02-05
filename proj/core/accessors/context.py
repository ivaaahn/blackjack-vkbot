import json
from typing import Union, Optional

from .base import BaseGameAccessor
from aioredis import client

from ..states import State

__all__ = ("GameCtxAccessor",)

STATE_PREFIX = "STATE_"
DATA_PREFIX = "DATA_"


def state_key(chat: int) -> str:
    return STATE_PREFIX + str(chat)


def data_key(chat: int) -> str:
    return DATA_PREFIX + str(chat)


class GameCtxAccessor(BaseGameAccessor):
    @property
    def cli(self) -> client.Redis:
        return self.store.redis.client

    async def set_state(self, chat: int, state: Union[State, int]) -> None:
        if isinstance(state, State):
            state = state.state_id

        await self.cli.set(state_key(chat), state)

    async def get_state(
        self, chat: int, default: Optional[int] = None
    ) -> Optional[int]:
        result = await self.cli.get(state_key(chat))
        return default if result is None else int(result)

    async def set_data(self, chat: int, data: dict) -> None:
        await self.cli.set(data_key(chat), json.dumps(data))

    async def get_data(
        self, chat: int, default: Optional[dict] = None
    ) -> Optional[dict]:
        if (data_json := await self.cli.get(data_key(chat))) is not None:
            return json.loads(data_json)
        return default

    async def update_data(self, chat: int, data: dict) -> None:
        pass

    async def reset_data(self, chat: int) -> None:
        await self.cli.delete(data_key(chat))

    async def reset_state(self, chat: int) -> None:
        await self.cli.delete(state_key(chat))
