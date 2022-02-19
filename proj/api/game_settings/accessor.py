from typing import Optional, Mapping, Type, Union

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError

from proj.store import ApiStore, CoreStore
from proj.store.base.accessor import ConnectAccessor

from .config import ConfigType, GameSettingsConfig
from .models import GameSettingsModel

__all__ = ("GameSettingsAccessor",)

from ...store.base import S


class GameSettingsAccessor(ConnectAccessor[S, ConfigType]):
    _DEFAULT_ID = 0

    class Meta:
        name = "game_settings"

    def __init__(
        self,
        store: Union[ApiStore, CoreStore],
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = GameSettingsConfig,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)

    @property
    def mongo_coll(self) -> AsyncIOMotorCollection:
        return self.store.mongo.game_settings_coll

    async def _connect(self) -> None:
        model = GameSettingsModel(
            _id=self._DEFAULT_ID,
            min_bet=self.config.min_bet,
            max_bet=self.config.max_bet,
            start_cash=self.config.start_cash,
            bonus=self.config.bonus,
            bonus_period=self.config.bonus_period,
            num_of_decks=self.config.num_of_decks,
        )

        try:
            await self.mongo_coll.insert_one(model.to_dict())
        except DuplicateKeyError:
            pass

    async def get(self, _id: int) -> Optional[GameSettingsModel]:
        _id = self._DEFAULT_ID
        raw = await self.mongo_coll.find_one({"_id": _id})
        return GameSettingsModel.from_dict(raw) if raw else None

    async def patch(self, _id: int, data: dict) -> None:
        await self.mongo_coll.update_one({"_id": _id}, {"$set": data})
