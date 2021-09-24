import json

from app.base.base_game_accessor import BaseGameAccessor
from typing import TYPE_CHECKING, Union, Optional

from app.game.states import State

if TYPE_CHECKING:
    from app.app import Application

STATE_PREFIX = 'STATE_'
DATA_PREFIX = 'DATA_'


def state_key(chat: int) -> str:
    return STATE_PREFIX + str(chat)


def data_key(chat: int) -> str:
    return DATA_PREFIX + str(chat)


class RedisGameAccessor(BaseGameAccessor):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)
        self.app = app

    @property
    def db(self):
        return self.app.redis.client

    async def connect(self, app: "Application"):
        pass

    async def disconnect(self, app: "Application"):
        pass

    async def set_state(self, chat: int, state: Union[State, int]) -> None:
        if isinstance(state, State):
            state = state.state_id

        await self.db.set(state_key(chat), state)

    async def get_state(self, chat: int, default: Optional[int] = None) -> Optional[int]:
        result = await self.db.get(state_key(chat))
        return default if result is None else int(result)

    async def set_data(self, chat: int, data: dict) -> None:
        await self.db.set(data_key(chat), json.dumps(data))

    async def get_data(self, chat: int, default: Optional[dict] = None) -> Optional[dict]:
        if (data_json := await self.db.get(data_key(chat))) is not None:
            return json.loads(data_json)
        return default

    async def update_data(self, chat: int, data: dict) -> None:
        pass

    async def reset_data(self, chat: int) -> None:
        await self.db.delete(data_key(chat))

    async def reset_state(self, chat: int) -> None:
        await self.db.delete(state_key(chat))
