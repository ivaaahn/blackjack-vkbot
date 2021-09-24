import json
import re
from enum import Enum
from typing import Optional

from app.store.vk_api.dataclasses import UpdateMessage


class CheckType(Enum):
    EQ = 0
    IN = 1


class Choices(str, Enum):
    HIT = 'hit'
    STAND = 'stand'
    BJ_PICK_UP11 = 'pick up 11'
    BJ_PICK_UP32 = 'pick up 32'
    BJ_WAIT = 'wait'


def get_username_by_id(user_id: int, chat: dict) -> str:
    return [p['first_name'] for p in chat['response']['profiles'] if p['id'] == user_id][0]


def parse_bet_expr(text: str) -> Optional[int]:
    numbers = [int(x) for x in re.findall(r'\d+', text)]
    return numbers[0] if numbers else None


def get_payload(msg: UpdateMessage, key: str = 'button') -> Optional[str]:
    if msg.payload is None:
        return None

    payload_json = json.loads(msg.payload)
    return payload_json.get(key)


def check_payload(msg: UpdateMessage, check_type: CheckType, eq_obj=None, in_obj=None) -> bool:
    value = get_payload(msg)

    if check_type is CheckType.EQ:
        return value == eq_obj
    elif check_type is CheckType.IN:
        return value in in_obj
    else:
        return False
