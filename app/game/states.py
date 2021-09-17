import itertools
from functools import wraps
from typing import Optional, Callable, TYPE_CHECKING

from app.game.keyboards import TextButton, Keyboard, ButtonColor

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

    def __init__(self, handler: Optional[Callable] = None, keyboard: Keyboard = Keyboard()) -> None:
        self._handler = handler
        self._keyboard = keyboard
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

    @property
    def keyboard(self) -> Optional[Keyboard]:
        return self._keyboard

    def register(self, func: Callable):
        self._handler = func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper


class BJStates:
    WAITING_FOR_TRIGGER = State(
        keyboard=Keyboard(one_time=False, buttons=[
            [
                TextButton(label='Новая игра', color=ButtonColor.POSITIVE, payload='{"button": "new_game"}'),
                # TextButton(label='Статистика', color=ButtonColor.NEGATIVE, payload='{"button": "stat"}'),
            ],
            [
                TextButton(label='Отмена', color=ButtonColor.NEGATIVE, payload='{"button": "cancel"}'),
            ],
        ]))

    WAITING_FOR_NEW_GAME = State(
        keyboard=Keyboard(one_time=False, buttons=[
            [
                TextButton(label='Один игрок', color=ButtonColor.PRIMARY, payload='{"button": "1"}'),
            ],
            [
                TextButton(label='Два игрока', color=ButtonColor.PRIMARY, payload='{"button": "2"}'),
                TextButton(label='Три игрока', color=ButtonColor.PRIMARY, payload='{"button": "3"}'),
            ],
            [
                TextButton(label='Отмена', color=ButtonColor.NEGATIVE, payload='{"button": "cancel"}'),
                # TextButton(label='Назад', color=ButtonColor.NEGATIVE, payload='{"button": "back"}'),
            ],
        ]))

    WAITING_FOR_PLAYERS_COUNT = State(
        keyboard=Keyboard(
            inline=True,
            one_time=False,
            buttons=[
                [
                    TextButton(label='Участвую!', color=ButtonColor.POSITIVE, payload='{"button": "register"}'),
                ],
                [
                    TextButton(label='Отменить игру', color=ButtonColor.NEGATIVE, payload='{"button": "cancel"}'),
                ],
            ]))

    WAITING_FOR_REGISTER = State()
    WAITING_FOR_BETS = State()
    WAITING_FOR_ACTION = State(
        keyboard=Keyboard(
            inline=True,
            one_time=False,
            buttons=[
                [
                    TextButton(label='Еще', color=ButtonColor.POSITIVE, payload='{"button": "hit"}'),
                    TextButton(label='Хватит', color=ButtonColor.NEGATIVE, payload='{"button": "stand"}'),
                ],
            ]))

    WAITING_FOR_ANSWER_TO_REPEAT_QUESTION = State(
        keyboard=Keyboard(
            one_time=False,
            buttons=[
                [
                    TextButton(label='Играем еще', color=ButtonColor.POSITIVE, payload='{"button": "play"}'),
                    TextButton(label='Больше не играем', color=ButtonColor.NEGATIVE, payload='{"button": "stop"}'),
                ],
            ]))
