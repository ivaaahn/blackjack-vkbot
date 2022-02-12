from dataclasses import dataclass
from typing import TypeVar


@dataclass
class AdminConfig:
    email: str
    password: str


ConfigType = TypeVar("ConfigType", bound=AdminConfig)
