import itertools
from functools import wraps
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.game.dataclasses import GAccessors
    from app.game.game import GameCtxProxy


class StateResolver:
    _STATES: dict[int, 'State'] = {}

    @classmethod
    def add_state(cls, state: 'State') -> None:
        cls._STATES[state.state_id] = state

    @classmethod
    def get_state(cls, state_id: int) -> Optional['State']:
        return cls._STATES.get(state_id)


class State:
    _id_iter = itertools.count()

    def __init__(self, handler: Optional[Callable] = None) -> None:
        self._handler = handler
        self._id = next(self._id_iter)
        StateResolver.add_state(self)

    @property
    def state_id(self) -> int:
        return self._id

    @property
    def handler(self) -> Callable[['GameCtxProxy', 'GAccessors'], None]:
        return self._handler

    @handler.setter
    def handler(self, value: Callable):
        self._handler = value

    def register(self, func: Callable):
        self._handler = func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper


class States:
    WAITING_FOR_TRIGGER = State()
    WAITING_FOR_START_CHOICE = State()
    WAITING_FOR_ACTIONS_IN_LK = State()
    WAITING_FOR_PLAYERS_AMOUNT = State()
    WAITING_FOR_REGISTRATION = State()
    WAITING_FOR_BETS = State()
    WAITING_FOR_ACTION = State()
    WAITING_FOR_LAST_CHOICE = State()
