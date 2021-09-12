from dataclasses import dataclass

# Базовые структуры, для выполнения задания их достаточно,
# поэтому постарайтесь не менять их пожалуйста из-за возможных проблем с тестами
from typing import Optional

from app.game.keyboards import Keyboard


@dataclass
class Message:
    peer_id: int
    text: str
    user_id: Optional[int] = None
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
