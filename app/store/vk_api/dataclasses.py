from dataclasses import dataclass
from typing import Optional
from app.game.keyboards import Keyboard
from datetime import date


@dataclass
class User:
    vk_id: int
    first_name: str
    last_name: str
    city: Optional[str]
    birthday: Optional[date] = None

    @staticmethod
    def from_dict(raw: dict) -> 'User':
        return User(
            first_name=raw['first_name'],
            last_name=raw['last_name'],
            city=raw['city']['title'] if raw.get('city') else None,
            birthday=User.parse_vk_date(raw.get('bdate')),
            vk_id=raw['id']
        )

    @staticmethod
    def parse_vk_date(raw: Optional[str]) -> date:
        if raw is None:
            return None

        split = raw.split('.')

        if len(split) == 2:
            return date.fromisoformat(f'--{split[1]}-{split[0]}')

        return date.fromisoformat(f'{split[2]}-{split[1]}-{split[0]}')


@dataclass
class Message:
    peer_id: int
    text: str
    kbd: Optional[Keyboard] = Keyboard()
    photos: Optional[str] = ''


@dataclass
class UpdateMessage:
    from_id: int
    peer_id: int
    text: str
    id: int
    payload: Optional[str]


@dataclass
class UpdateObject:
    message: UpdateMessage


@dataclass
class Update:
    type: str
    object: UpdateObject
