import json
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Optional


class ButtonColor(str, Enum):
    PRIMARY = 'primary',
    SECONDARY = 'secondary',
    NEGATIVE = 'negative',
    POSITIVE = 'positive',


class AbstractButton(metaclass=ABCMeta):
    def __init__(self, color: ButtonColor) -> None:
        self._color = color
        self._type = None

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class TextButton(AbstractButton):
    def __init__(self, label: str, color: ButtonColor, payload: Optional[str] = None) -> None:
        super().__init__(color)
        self._type = 'text'
        self._label = label
        self._payload = payload

    def to_dict(self) -> dict:
        return {
            'color': self._color,
            'action': {
                'type': self._type,
                'label': self._label,
                'payload': self._payload,
            },
        }


class Keyboard:
    def __init__(self, one_time: bool = True, inline: bool = False,
                 buttons: Optional[list[list[AbstractButton]]] = None) -> None:
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
            'one_time': self._one_time,
            'inline': self._inline,
            'buttons': [[btn.to_dict() for btn in btn_line] for btn_line in self._buttons]
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
