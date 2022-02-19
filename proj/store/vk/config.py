from dataclasses import dataclass
from typing import TypeVar


@dataclass
class VkBotConfig:
    token: str
    group_id: int


ConfigType = TypeVar("ConfigType", bound=VkBotConfig)
