import json
import random
from typing import Optional

import aiohttp
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.config import BotConfig, Config
from app.databases import Databases
from app.store.vk_api.dataclasses import Message, User
from app.app_logger import get_logger

logger = get_logger(__file__)


class VkApiAccessor(BaseAccessor):
    def __init__(self, databases: Databases, config: Config):
        super().__init__(databases, config)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.ts: Optional[int] = None

    @property
    def cfg(self) -> BotConfig:
        return self.config.bot

    async def connect(self):
        logger.info("VkApi accessor connected")
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        await self._get_long_poll_service()

    async def disconnect(self):
        logger.info("VkApi accessor disconnected")

        if self.session is not None:
            await self.session.close()
            self.session = None

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"

        url += "&".join(
            f'{k}={v if not isinstance(v, list) else ",".join(tuple(map(str, v)))}'
            for k, v in params.items()
        )

        return url

    async def _get_long_poll_service(self):
        group_id = self.cfg.group_id
        token = self.cfg.token

        query = self._build_query(
            host="https://api.vk.com/",
            method="method/groups.getLongPollServer",
            params={"group_id": group_id, "access_token": token},
        )

        async with self.session.get(query) as response:
            response_body = (await response.json())["response"]
            self.key = response_body["key"]
            self.server = response_body["server"]
            self.ts = response_body["ts"]

    async def poll(self) -> str:
        query = self._build_query(
            host=self.server,
            method="",
            params={
                "act": "a_check",
                "key": self.key,
                "wait": 25,
                "mode": 2,
                "ts": self.ts,
            },
        )

        async with self.session.get(query) as response:
            resp_json: dict = await response.json()
            self.ts = resp_json["ts"]
            raw_updates = resp_json["updates"]

        return json.dumps(resp_json)

    async def send_message(self, message: Message) -> None:
        query_params = {
            "message": message.text,
            "access_token": self.cfg.token,
            "random_id": random.randint(-2147483648, 2147483648),
            "peer_id": message.peer_id,
            "keyboard": message.kbd.serialize(),
            "attachment": message.photos,
        }

        query = self._build_query(
            host="https://api.vk.com/",
            method="method/messages.send",
            params=query_params,
        )

        async with self.session.get(query) as resp:
            _ = await resp.json()

    async def get_chat(self, peer_id: int) -> dict:
        query = self._build_query(
            host="https://api.vk.com/",
            method="method/messages.getConversationMembers",
            params={
                "access_token": self.cfg.token,
                "peer_id": peer_id,
            },
        )

        async with self.session.get(query) as resp:
            return await resp.json()

    async def get_conversations(self):
        query = self._build_query(
            host="https://api.vk.com/",
            method="method/messages.getConversations",
            params={
                "access_token": self.cfg.token,
            },
        )

        async with self.session.get(query) as resp:
            return await resp.json()
            # return await resp.json()

    async def get_users(self, vk_ids: list[int]) -> list[User]:
        query = self._build_query(
            host="https://api.vk.com/",
            method="method/users.get",
            params={
                "access_token": self.cfg.token,
                "user_ids": vk_ids,
                "fields": [
                    "bdate",
                    "city",
                ],
            },
        )

        async with self.session.get(query) as resp:
            data = await resp.json()

        return [User.from_dict(u) for u in data["response"]]
