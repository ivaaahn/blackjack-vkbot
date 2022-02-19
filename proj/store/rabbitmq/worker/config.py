from dataclasses import dataclass
from typing import TypeVar


@dataclass
class RabbitMQWorkerConfig:
    host: str
    port: int
    user: str
    password: str
    queue_name: str
    reconnect_timeout: int = 5
    capacity: int = 1


ConfigType = TypeVar("ConfigType", bound=RabbitMQWorkerConfig)
