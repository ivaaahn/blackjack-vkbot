from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class PlayerModel:
    vk_id: int
    chat_id: int
    first_name: str
    last_name: str
    cash: float
    last_bonus_date: datetime
    registered_at: datetime
    city: Optional[str] = None
    birthday: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            'vk_id': self.vk_id,
            'chat_id': self.chat_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registered_at': self.registered_at,
            'last_bonus_date': self.last_bonus_date,
            'birthday': self.birthday,
            'city': self.city,
            'cash': self.cash,
        }

    @staticmethod
    def from_dict(raw: dict) -> 'PlayerModel':
        return PlayerModel(
            vk_id=raw['vk_id'],
            chat_id=raw['chat_id'],
            first_name=raw['first_name'],
            last_name=raw['last_name'],
            registered_at=raw['registered_at'],
            last_bonus_date=raw['last_bonus_date'],
            birthday=raw['birthday'],
            city=raw['city'],
            cash=raw['cash'],
        )

    def check_bonus(self, minutes: int) -> bool:
        return datetime.now() - self.last_bonus_date > timedelta(minutes=minutes)

    def __str__(self) -> str:
        return f'[id{self.vk_id}|{self.first_name} {self.last_name}] - {self.cash}$'


