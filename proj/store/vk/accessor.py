import json
import random
from typing import Optional, Mapping, Type

import aiohttp
from aiohttp.client import ClientSession

from proj.store import BaseStore
from proj.store.base.accessor import ConnectAccessor
from proj.store.vk.config import ConfigType, VkBotConfig
from .dataclasses import Message, User


class VkAccessor(ConnectAccessor[BaseStore, ConfigType]):
    class Meta:
        name = "vk"

    def __init__(
        self,
        store: BaseStore,
        *,
        name: Optional[str] = None,
        config: Optional[Mapping] = None,
        config_type: Type[ConfigType] = VkBotConfig,
    ):
        super().__init__(store, name=name, config=config, config_type=config_type)
        self._session: Optional[ClientSession] = None
        self._key: Optional[str] = None
        self._server: Optional[str] = None
        self._ts: Optional[int] = None

    async def _connect(self):
        self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))

        await self._get_long_poll_service()

    async def _disconnect(self):
        if self._session:
            self.logger.debug("VK SESSION CLOSED")
            await self._session.close()
            self._session = None

    @staticmethod
    def _build_query(
        method: str, params: dict, host: str = "https://api.vk.com/"
    ) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"

        url += "&".join(
            f'{k}={v if not isinstance(v, list) else ",".join(tuple(map(str, v)))}'
            for k, v in params.items()
        )

        return url

    async def _get_long_poll_service(self):
        query = self._build_query(
            method="method/groups.getLongPollServer",
            params={
                "group_id": self.config.group_id,
                "access_token": self.config.token,
            },
        )

        async with self._session.get(query) as response:
            response_body = (await response.json())["response"]

            print(response_body)

            self._key = response_body["key"]
            self._server = response_body["server"]
            self._ts = response_body["ts"]

    async def poll(self) -> dict:
        query = self._build_query(
            host=self._server,
            method="",
            params={
                "act": "a_check",
                "key": self._key,
                "wait": 25,
                "mode": 2,
                "ts": self._ts,
            },
        )

        async with self._session.get(
            query
        ) as response:  # TODO мб это проверить,валидиторвать?
            resp_json: dict = await response.json()
            self._ts = resp_json["ts"]
            raw_updates = resp_json["updates"]

        return resp_json

    async def send_message(self, message: Message) -> None:
        query_params = {
            "message": message.text,
            "access_token": self.config.token,
            "random_id": random.randint(-2147483648, 2147483648),
            "peer_id": message.peer_id,
            "keyboard": message.kbd.serialize(),
            "attachment": message.photos,
        }

        query = self._build_query(
            method="method/messages.send",
            params=query_params,
        )

        async with self._session.get(query) as resp:
            _ = await resp.json()

    async def get_chat(self, peer_id: int) -> dict:
        query = self._build_query(
            method="method/messages.getConversationMembers",
            params={
                "access_token": self.config.token,
                "peer_id": peer_id,
            },
        )

        async with self._session.get(query) as resp:
            return await resp.json()

    async def get_conversations(self):
        query = self._build_query(
            method="method/messages.getConversations",
            params={
                "access_token": self.config.token,
            },
        )

        async with self._session.get(query) as resp:
            return await resp.json()
            # return await resp.json()

    async def get_users(self, vk_ids: list[int]) -> list[User]:
        query = self._build_query(
            method="method/users.get",
            params={
                "access_token": self.config.token,
                "user_ids": vk_ids,
                "fields": [
                    "bdate",
                    "city",
                ],
            },
        )

        async with self._session.get(query) as resp:
            data = await resp.json()

        return [User.from_dict(u) for u in data["response"]]
