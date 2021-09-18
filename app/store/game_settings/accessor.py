import typing
from typing import Optional

from pymongo.errors import DuplicateKeyError

from app.api.settings.models import GameSettingsModel
from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.app import Application
    from app.config import GameConfig
    from motor.motor_asyncio import AsyncIOMotorCollection


class GameSettingsAccessor(BaseAccessor):
    _DEFAULT_ID = 0

    def __init__(self, app: "Application") -> None:
        super().__init__(app)

    @property
    def collect(self) -> "AsyncIOMotorCollection":
        return self.app.mongo.collects.game_settings

    @property
    def game_cfg(self) -> 'GameConfig':
        return self.app.config.game

    async def connect(self, app: "Application") -> None:
        await self.install(
            min_bet=self.game_cfg.min_bet,
            max_bet=self.game_cfg.max_bet,
            start_cash=self.game_cfg.start_cash,
            bonus=self.game_cfg.bonus,
            bonus_period=self.game_cfg.bonus_period,
            num_of_decks=self.game_cfg.num_of_decks,
        )

    async def disconnect(self, app: "Application") -> None:
        pass

    async def install(self, min_bet: float, max_bet: float, start_cash: float, bonus: float,
                      num_of_decks: int, bonus_period) -> None:

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
            await self.collect.insert_one(model.to_dict())
        except DuplicateKeyError:
            pass

    async def get(self, _id: int) -> Optional[GameSettingsModel]:
        _id = self._DEFAULT_ID
        raw = await self.collect.find_one({'_id': _id})

        if raw is not None:
            return GameSettingsModel.from_dict(raw)

        return None
