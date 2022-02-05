from dataclasses import dataclass
from typing import TypeVar

__all__ = ("RedisConfig",)


@dataclass
class RedisConfig:
    host: str
    port: int
    user: str = "redis"
    password: str = "redis"
    db: int = 0
    reconnect_timeout: int = 5


ConfigType = TypeVar("ConfigType", bound=RedisConfig)
