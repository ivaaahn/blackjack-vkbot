from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

from .keyboards import Keyboard


@dataclass
class User:
    vk_id: int
    first_name: str
    last_name: str
    city: Optional[str]
    birthday: Optional[date] = None

    @staticmethod
    def from_dict(raw: dict) -> "User":
        return User(
            first_name=raw["first_name"],
            last_name=raw["last_name"],
            city=raw["city"]["title"] if raw.get("city") else None,
            birthday=User.parse_vk_date(raw.get("bdate")),
            vk_id=raw["id"],
        )

    @staticmethod
    def parse_vk_date(raw: Optional[str]) -> Optional[datetime]:
        if raw is None:
            return None

        split = tuple(map(int, raw.split(".")))

        if len(split) == 2:
            return datetime.fromisoformat(f"1900-{split[1]:02d}-{split[0]:02d}")

        return datetime.fromisoformat(f"{split[2]}-{split[1]:02d}-{split[0]:02d}")


@dataclass
class Message:
    peer_id: int
    text: str
    kbd: Optional[Keyboard] = Keyboard()
    photos: Optional[str] = ""


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
