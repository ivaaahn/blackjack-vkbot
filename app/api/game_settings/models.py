from dataclasses import dataclass


@dataclass
class GameSettingsModel:
    _id: int
    min_bet: float
    max_bet: float
    start_cash: float
    bonus: float
    bonus_period: int
    num_of_decks: int

    def to_dict(self) -> dict:
        return {
            '_id': self._id,
            'min_bet': self.min_bet,
            'max_bet': self.max_bet,
            'start_cash': self.start_cash,
            'bonus': self.bonus,
            'bonus_period': self.bonus_period,
            'num_of_decks': self.num_of_decks,
        }

    @staticmethod
    def from_dict(raw: dict) -> 'GameSettingsModel':
        return GameSettingsModel(
            _id=raw['_id'],
            min_bet=raw['min_bet'],
            max_bet=raw['max_bet'],
            start_cash=raw['start_cash'],
            bonus=raw['bonus'],
            bonus_period=raw['bonus_period'],
            num_of_decks=raw['num_of_decks'],
        )
