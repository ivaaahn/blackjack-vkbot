from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError

from app.api.game_settings.models import GameSettingsModel
from app.base.mongo_accessor import MongoAccessor
from app.config import GameConfig, Config
from app.databases import Databases
from app.app_logger import get_logger

logger = get_logger(__file__)


class GameSettingsAccessor(MongoAccessor):
    _DEFAULT_ID = 0

    def __init__(self, databases: Databases, config: Config) -> None:
        super().__init__(databases, config)

    @property
    def coll(self) -> AsyncIOMotorCollection:
        return self.mongo.collects.game_settings

    @property
    def cfg(self) -> GameConfig:
        return self.config.game

    async def connect(self) -> None:
        logger.info("Game settings accessor connected")
        await self.install(
            min_bet=self.cfg.min_bet,
            max_bet=self.cfg.max_bet,
            start_cash=self.cfg.start_cash,
            bonus=self.cfg.bonus,
            bonus_period=self.cfg.bonus_period,
            num_of_decks=self.cfg.num_of_decks,
        )

    async def install(
        self,
        min_bet: float,
        max_bet: float,
        start_cash: float,
        bonus: float,
        num_of_decks: int,
        bonus_period,
    ) -> None:

        model = GameSettingsModel(
            _id=self._DEFAULT_ID,
            min_bet=min_bet,
            max_bet=max_bet,
            start_cash=start_cash,
            bonus=bonus,
            num_of_decks=num_of_decks,
            bonus_period=bonus_period,
        )

        try:
            await self.coll.insert_one(model.to_dict())
        except DuplicateKeyError:
            pass

    async def get(self, _id: int) -> Optional[GameSettingsModel]:
        _id = self._DEFAULT_ID
        raw = await self.coll.find_one({"_id": _id})
        return GameSettingsModel.from_dict(raw) if raw else None

    async def patch(self, _id: int, data: dict) -> None:
        await self.coll.update_one({"_id": _id}, {"$set": data})
