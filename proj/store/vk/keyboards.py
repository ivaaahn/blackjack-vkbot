import json
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Optional

from proj.core.types import (
    StartActionChoiceType,
    MainActionChoiceType,
    LastActionChoiceType,
)


class ButtonColor(str, Enum):
    PRIMARY = ("primary",)
    SECONDARY = ("secondary",)
    NEGATIVE = ("negative",)
    POSITIVE = ("positive",)


class AbstractButton(metaclass=ABCMeta):
    def __init__(self, color: ButtonColor) -> None:
        self._color = color
        self._type = None

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class TextButton(AbstractButton):
    def __init__(
        self, label: str, color: ButtonColor, payload: Optional[str] = None
    ) -> None:
        super().__init__(color)
        self._type = "text"
        self._label = label
        self._payload = payload

    def to_dict(self) -> dict:
        return {
            "color": self._color,
            "action": {
                "type": self._type,
                "label": self._label,
                "payload": self._payload,
            },
        }


class Keyboard:
    def __init__(
        self,
        one_time: bool = True,
        inline: bool = False,
        buttons: Optional[list[list[AbstractButton]]] = None,
    ) -> None:
        self._buttons = [] if buttons is None else buttons
        self._one_time = one_time
        self._inline = inline

    def add_line(self) -> None:
        if self._buttons[-1]:
            self._buttons.append([])

    def add_button(self, btn: AbstractButton) -> None:
        self._buttons[-1].append(btn)

    def to_dict(self) -> dict:
        return {
            "one_time": self._one_time,
            "inline": self._inline,
            "buttons": [
                [btn.to_dict() for btn in btn_line] for btn_line in self._buttons
            ],
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict())


class Keyboards:
    EMPTY = Keyboard()

    START = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Начать игру",
                    color=ButtonColor.POSITIVE,
                    payload=f'{"button": "{StartActionChoiceType.new_game}"}',
                ),
            ],
            [
                TextButton(
                    label="Забрать бонус",
                    color=ButtonColor.PRIMARY,
                    payload=f'{"button": "{StartActionChoiceType.get_bonus}"}',
                ),
            ],
            [
                TextButton(
                    label="Проверить счёт",
                    color=ButtonColor.PRIMARY,
                    payload=f'{"button": "{StartActionChoiceType.show_balance}"}',
                ),
            ],
            [
                TextButton(
                    label="Статистика",
                    color=ButtonColor.PRIMARY,
                    payload=f'{"button": "{StartActionChoiceType.common_statistic}"}',
                ),
            ],
            [
                TextButton(
                    label="Моя статистика",
                    color=ButtonColor.PRIMARY,
                    payload=f'{"button": "{StartActionChoiceType.personal_statistic}"}',
                ),
            ],
            [
                TextButton(
                    label="Выход",
                    color=ButtonColor.NEGATIVE,
                    payload=f'{"button": "{StartActionChoiceType.cancel}"}',
                ),
            ],
        ],
    )

    OKAY = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Окей", color=ButtonColor.NEGATIVE, payload='{"button": "ok"}'
                ),
            ],
        ],
    )

    GET_OUT = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Встать из-за стола",
                    color=ButtonColor.NEGATIVE,
                    payload='{"button": "leaving the game"}',
                ),
            ],
        ],
    )

    BJ_DEALER_WITH_ACE = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Забрать 1 к 1",
                    color=ButtonColor.NEGATIVE,
                    payload=f'{"button": "{MainActionChoiceType.blackjack_pickup11}"}',
                ),
                TextButton(
                    label="Дождаться конца игры",
                    color=ButtonColor.NEGATIVE,
                    payload='{"button": "wait"}',
                ),
            ],
        ],
    )

    BJ_DEALER_WITHOUT_ACE = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Окей",
                    color=ButtonColor.NEGATIVE,
                    payload='{"button": "wait"}',
                ),
            ],
        ],
    )

    BJ_WIN_32 = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Забрать 3 к 2",
                    color=ButtonColor.NEGATIVE,
                    payload=f'{"button": "{MainActionChoiceType.blackjack_pickup32}"}',
                ),
            ],
        ],
    )

    NUMBER_OF_PLAYERS = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Один игрок",
                    color=ButtonColor.PRIMARY,
                    payload='{"button": "1"}',
                ),
            ],
            [
                TextButton(
                    label="Два игрока",
                    color=ButtonColor.PRIMARY,
                    payload='{"button": "2"}',
                ),
                TextButton(
                    label="Три игрока",
                    color=ButtonColor.PRIMARY,
                    payload='{"button": "3"}',
                ),
            ],
            [
                TextButton(
                    label="Отменить игру",
                    color=ButtonColor.NEGATIVE,
                    payload='{"button": "cancel"}',
                ),
            ],
        ],
    )

    CONFIRM = Keyboard(
        inline=False,
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Я в игре!",
                    color=ButtonColor.POSITIVE,
                    payload='{"button": "register"}',
                ),
            ],
            [
                TextButton(
                    label="Отменить игру",
                    color=ButtonColor.NEGATIVE,
                    payload='{"button": "cancel"}',
                ),
            ],
        ],
    )

    CHOOSE_ACTION = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Ещё",
                    color=ButtonColor.POSITIVE,
                    payload=f'{"button": "{MainActionChoiceType.hit}"}',
                ),
                TextButton(
                    label="Хватит",
                    color=ButtonColor.NEGATIVE,
                    payload=f'{"button": "{MainActionChoiceType.stand}"}',
                ),
            ],
        ],
    )

    REPEAT_GAME_QUESTION = Keyboard(
        one_time=False,
        buttons=[
            [
                TextButton(
                    label="Играем еще",
                    color=ButtonColor.POSITIVE,
                    payload=f'{"button": "{LastActionChoiceType.repeat_game}"}',
                ),
                TextButton(
                    label="Больше не играем",
                    color=ButtonColor.NEGATIVE,
                    payload=f'{"button": "{LastActionChoiceType.end_game}"}',
                ),
            ],
        ],
    )
