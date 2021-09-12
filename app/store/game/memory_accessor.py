from typing import Optional, Union
import typing

from app.base.base_game_accessor import BaseGameAccessor
from app.game.states import State

if typing.TYPE_CHECKING:
    from app.web.app import Application


class MemoryGameAccessor(BaseGameAccessor):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)
        self.app = app

    @property
    def db(self):
        return self.app.database

    async def connect(self, app: "Application"):
        pass

    async def disconnect(self, app: "Application"):
        pass

    async def set_state(self, chat: int, state: Union[State, int]) -> None:
        if isinstance(state, State):
            state = state.state_id

        self.db.states[chat] = state

    async def get_state(self, chat: int, default: Optional[int] = None) -> Optional[int]:
        return self.db.states.get(chat, default)

    async def set_data(self, chat: int, data: dict) -> None:
        self.db.game_data[chat] = data

    async def get_data(self, chat: int, default: Optional[dict] = None) -> Optional[dict]:
        return self.db.game_data.get(chat, default)

    async def update_data(self, chat: int, data: dict) -> None:
        self.db.game_data[chat].update(data)

    async def reset_data(self, chat: int) -> None:
        self.db.game_data.pop(chat, None)

    async def reset_state(self, chat: int) -> None:
        self.db.states.pop(chat, None)
