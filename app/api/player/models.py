from datetime import datetime, date, timedelta
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class PlayerModel:
    _id: UUID
    vk_id: int
    first_name: str
    last_name: str
    city: str
    cash: float
    last_bonus_date: datetime
    registered_at: datetime
    birthday: Optional[date] = None

    def to_dict(self) -> dict:
        return {
            '_id': self._id,
            'vk_id': self.vk_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registered_at': str(self.registered_at),
            'last_bonus_date': str(self.last_bonus_date),
            'birthday': str(self.birthday),
            'city': self.city,
            'cash': self.cash,
        }

    @staticmethod
    def from_dict(raw: dict) -> 'PlayerModel':
        return PlayerModel(
            _id=raw['_id'],
            vk_id=raw['vk_id'],
            first_name=raw['first_name'],
            last_name=raw['last_name'],
            registered_at=datetime.fromisoformat(raw['registered_at']),
            last_bonus_date=datetime.fromisoformat(raw['last_bonus_date']),
            birthday=date.fromisoformat(raw['birthday']),
            city=raw['city'],
            cash=raw['cash'],
        )

    def check_bonus(self, minutes: int) -> bool:
        return datetime.now() - self.last_bonus_date > timedelta(minutes=minutes)


