import datetime
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
    registered_at: datetime.datetime
    birthday: Optional[datetime.date] = None

    def to_dict(self) -> dict:
        return {
            '_id': self._id,
            'vk_id': self.vk_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registered_at': str(self.registered_at),
            'birthday': str(self.birthday),
            'city': self.city,
        }

    @staticmethod
    def from_dict(raw: dict) -> 'PlayerModel':
        return PlayerModel(
            _id=raw['_id'],
            vk_id=raw['vk_id'],
            first_name=raw['first_name'],
            last_name=raw['last_name'],
            registered_at=raw['registered_at'],
            birthday=raw['birthday'],
            city=raw['city']
        )

