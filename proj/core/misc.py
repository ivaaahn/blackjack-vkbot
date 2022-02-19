import json
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from proj.store.vk.dataclasses import UpdateMessage


class CheckType(Enum):
    EQ = 0
    IN = 1


def get_username_by_id(user_id: int, chat: dict) -> str:
    return [
        p["first_name"] for p in chat["response"]["profiles"] if p["id"] == user_id
    ][0]


def parse_bet_expr(text: str) -> Optional[int]:
    numbers = [int(x) for x in re.findall(r"\d+", text)]
    return numbers[0] if numbers else None


def get_payload(msg: UpdateMessage, key: str = "button") -> Optional[str]:
    if msg.payload is None:
        return None

    payload_json = json.loads(msg.payload)
    return payload_json.get(key)


def check_payload(
    msg: UpdateMessage, check_type: CheckType, eq_obj=None, in_obj=None
) -> bool:
    value = get_payload(msg)

    if check_type is CheckType.EQ:
        return value == eq_obj
    elif check_type is CheckType.IN:
        return value in in_obj
    else:
        return False


def check_back(payload: str) -> bool:
    return payload == "back"


def check_cancel(payload: str) -> bool:
    return payload == "cancel"


def pretty_datetime(raw: datetime) -> str:
    return raw.strftime("%b %d %Y в %I:%M%p")


def pretty_time_delta(timed: timedelta):
    seconds = timed.seconds
    sign_string = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%s%dd%dh%dm%ds" % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return "%s%dh%dm%ds" % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return "%s%dm%ds" % (sign_string, minutes, seconds)
    else:
        return "%s%ds" % (sign_string, seconds)
