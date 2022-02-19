from dataclasses import dataclass
from typing import TypeVar


@dataclass
class RabbitConfig:
    host: str
    port: int
    user: str
    password: str
    queue_name: str
    reconnect_timeout: int = 5


ConfigType = TypeVar("ConfigType", bound=RabbitConfig)
