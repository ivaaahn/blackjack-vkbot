from dataclasses import dataclass
from typing import Optional
from app.game.keyboards import Keyboard


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
