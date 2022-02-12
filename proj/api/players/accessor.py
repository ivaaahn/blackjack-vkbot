from datetime import datetime
from typing import Optional, Any, Type, Mapping, Union

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from proj.store import ApiStore, CoreStore
from proj.store.base.accessor import ConnectAccessor
from .models import PlayerModel, PlayerStats
from .pipelines import (
    group_by_chat_pipeline,
    match_pipeline,
    chat_pagination_pipeline,
)
from ..chats.models import ChatModel

__all__ = ("PlayersAccessor",)

from ..game_settings.config import GameSettingsConfig

from ...config import ConfigType
from ...store.base import S


class PlayersAccessor(ConnectAccessor[S, None]):
    class Meta:
        name = "players"

    def __init__(
        self,
        store: Union[ApiStore, CoreStore],
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = None,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)

    @property
    def mongo_coll(self) -> AsyncIOMotorCollection:
        return self.store.mongo.players_coll

    async def _connect(self) -> None:
        try:
            await self.mongo_coll.create_index(
                [("chat_id", ASCENDING), ("vk_id", ASCENDING)], unique=True
            )
            await self.mongo_coll.create_index([("chat_id", ASCENDING)])
            await self.mongo_coll.create_index([("cash", DESCENDING)])
        except:
            self.logger.info("Indexes for player collection have already created")
        else:
            self.logger.info("Indexes for player collection created")

    async def get_chat_by_id(self, chat_id: int) -> Optional[ChatModel]:
        pipeline = match_pipeline("chat_id", chat_id) + group_by_chat_pipeline()
        result = await self.mongo_coll.aggregate(pipeline).to_list(None)
        return ChatModel.from_dict(result[0]) if result else None

    async def get_player_by_vk_id(
        self, vk_id: int, chat_id: int
    ) -> Optional[PlayerModel]:
        # request = {'vk_id': vk_id} if chat_id is None else {'chat_id': chat_id, 'vk_id': vk_id}
        raw_player = await self.mongo_coll.find_one(
            {"chat_id": chat_id, "vk_id": vk_id}
        )
        return PlayerModel.from_dict(raw_player) if raw_player else None

    async def get_chats_list(
        self, offset: int, limit: int, order_by: Optional[str], order_type: int
    ) -> list[ChatModel]:

        pipeline = group_by_chat_pipeline() + chat_pagination_pipeline(
            offset, limit, order_by, order_type
        )
        result = await self.mongo_coll.aggregate(pipeline).to_list(None)
        return [ChatModel.from_dict(chat_raw) for chat_raw in result]

    async def get_players_list(
        self,
        offset: int,
        limit: int,
        order_by: str,
        order_type: int,
        vk_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> list[PlayerModel]:

        filter_ = {}

        if vk_id is not None:
            filter_["vk_id"] = vk_id

        if chat_id is not None:
            filter_["chat_id"] = chat_id

        cursor = (
            self.mongo_coll.find(filter_)
            .sort(order_by, order_type)
            .skip(offset)
            .limit(limit)
        )
        return [PlayerModel.from_dict(p_raw) for p_raw in await cursor.to_list(None)]

    async def patch(self, chat_id: int, vk_id: int, data: dict) -> None:
        await self.mongo_coll.update_one(
            {"chat_id": chat_id, "vk_id": vk_id}, {"$set": data}
        )

    async def update_cash(self, chat_id: int, vk_id: int, new_cash: float) -> None:
        await self.patch(chat_id, vk_id, {"cash": new_cash})

    async def get_player_position(
        self, chat_id: int, value: Any, field: str = "cash"
    ) -> Optional[int]:
        return (
            await self.mongo_coll.count_documents(
                {"$and": [{"chat_id": chat_id}, {field: {"$gt": value}}]}
            )
            + 1
        )

    async def update_after_game(
        self,
        chat_id: int,
        vk_id: int,
        new_cash: float,
        new_stats: PlayerStats,
    ) -> None:

        await self.patch(
            chat_id, vk_id, {"cash": new_cash, "stats": new_stats.to_dict()}
        )

    async def give_bonus(self, chat_id: int, vk_id: int, new_cash: float) -> None:
        await self.mongo_coll.update_one(
            {"chat_id": chat_id, "vk_id": vk_id},
            {"$set": {"last_bonus_date": datetime.utcnow(), "cash": new_cash}},
        )

    async def add_player(
        self,
        chat_id: int,
        vk_id: int,
        first_name: str,
        last_name: str,
        birthday: Optional[datetime],
        start_cash: float,
        city: Optional[str],
    ) -> None:

        try:
            await self.mongo_coll.insert_one(
                {
                    "vk_id": vk_id,
                    "chat_id": chat_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "registered_at": datetime.utcnow(),
                    "last_bonus_date": datetime.utcnow(),
                    "birthday": birthday,
                    "city": city,
                    "cash": start_cash,
                    "stats": PlayerStats(max_cash=start_cash).to_dict(),
                }
            )

        except DuplicateKeyError:
            pass
