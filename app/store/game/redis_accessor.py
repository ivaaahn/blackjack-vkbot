import json
from typing import Union, Optional

from app.base.base_game_accessor import BaseGameAccessor
from app.config import Config
from app.databases import Databases
from app.databases.redis import Redis
from app.game.states import State
from aioredis import client

STATE_PREFIX = 'STATE_'
DATA_PREFIX = 'DATA_'


def state_key(chat: int) -> str:
    return STATE_PREFIX + str(chat)


def data_key(chat: int) -> str:
    return DATA_PREFIX + str(chat)


class RedisGameAccessor(BaseGameAccessor):
    def __init__(self, databases: Databases, config: Config) -> None:
        super().__init__(databases, config)

    @property
    def redis(self) -> Redis:
        return self.databases.redis

    @property
    def client(self) -> client.Redis:
        return self.redis.client

    async def set_state(self, chat: int, state: Union[State, int]) -> None:
        if isinstance(state, State):
            state = state.state_id

        await self.client.set(state_key(chat), state)

    async def get_state(self, chat: int, default: Optional[int] = None) -> Optional[int]:
        result = await self.client.get(state_key(chat))
        return default if result is None else int(result)

    async def set_data(self, chat: int, data: dict) -> None:
        await self.client.set(data_key(chat), json.dumps(data))

    async def get_data(self, chat: int, default: Optional[dict] = None) -> Optional[dict]:
        if (data_json := await self.client.get(data_key(chat))) is not None:
            return json.loads(data_json)
        return default

    async def update_data(self, chat: int, data: dict) -> None:
        pass

    async def reset_data(self, chat: int) -> None:
        await self.client.delete(data_key(chat))

    async def reset_state(self, chat: int) -> None:
        await self.client.delete(state_key(chat))
