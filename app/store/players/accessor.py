import typing
from datetime import datetime, date
from typing import Optional
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from app.base.base_accessor import BaseAccessor
from app.api.player.models import PlayerModel

if typing.TYPE_CHECKING:
    from app.app import Application
    from app.config import GameConfig
    from motor.motor_asyncio import AsyncIOMotorCollection


class PlayersAccessor(BaseAccessor):
    def __init__(self, app: "Application") -> None:
        super().__init__(app)

    @property
    def collect(self) -> "AsyncIOMotorCollection":
        return self.app.mongo.collects.players

    @property
    def game_cfg(self) -> 'GameConfig':
        return self.app.config.game

    async def connect(self, app: "Application") -> None:
        pass

    async def disconnect(self, app: "Application") -> None:
        pass

    async def get_by_vk_id(self, vk_id: int) -> Optional[PlayerModel]:
        raw_player = await self.collect.find_one({'vk_id': vk_id})
        if raw_player is not None:
            return PlayerModel.from_dict(raw_player)
        return None

    async def update_cash(self, vk_id: int, new_cash: float):
        result = await self.collect.update_one({'vk_id': vk_id}, {'$set': {'cash': new_cash}})
        print('updated %s document' % result.modified_count)

    async def give_bonus(self, vk_id: int, new_cash: float):
        result = await self.collect.update_one(
            {
                'vk_id': vk_id,
            },
            {
                '$set': {
                    'last_bonus_date': str(datetime.now()),
                    'cash': new_cash,
                }
            }
        )
        print('updated %s document' % result.modified_count)

    async def add(self,
                  vk_id: int,
                  first_name: str,
                  last_name: str,
                  birthday: Optional[date],
                  start_cash: float,
                  city: Optional[str]):

        model = PlayerModel(
            _id=uuid4(),
            vk_id=vk_id,
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            registered_at=datetime.now(),
            city=city,
            cash=start_cash,
            last_bonus_date=datetime.now(),
        )

        try:
            await self.collect.insert_one(model.to_dict())
        except DuplicateKeyError:
            print('duplicate')
