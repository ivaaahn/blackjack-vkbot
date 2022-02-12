from dataclasses import dataclass
from typing import TypeVar


@dataclass
class GameSettingsConfig:
    start_cash: float
    bonus: float
    bonus_period: int
    min_bet: float
    max_bet: float
    num_of_decks: int


ConfigType = TypeVar("ConfigType", bound=GameSettingsConfig)
