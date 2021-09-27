import asyncio

import aiohttp
import json

from typing import Optional
from aiohttp.client import ClientSession
from .config import BotConfig


class VkApiAccessor:
    def __init__(self, bot_config: BotConfig):
        self.bot_cfg = bot_config
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.ts: Optional[int] = None

    async def connect(self):
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        await self._get_long_poll_service()

    async def disconnect(self):
        if self.session is not None:
            await self.session.close()
            self.session = None

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"

        url += '&'.join(
            f'{k}={v if not isinstance(v, list) else ",".join(tuple(map(str, v)))}' for k, v in params.items())

        return url

    async def _get_long_poll_service(self):
        group_id = self.bot_cfg.group_id
        token = self.bot_cfg.token

        query = self._build_query(
            host='https://api.vk.com/',
            method='method/groups.getLongPollServer',
            params={'group_id': group_id, 'access_token': token}
        )

        async with self.session.get(query) as response:
            response_body = (await response.json())['response']
            self.key = response_body['key']
            self.server = response_body['server']
            self.ts = response_body['ts']

    async def poll(self) -> str:
        query = self._build_query(
            host=self.server,
            method='',
            params={
                'act': 'a_check',
                'key': self.key,
                'wait': 25,
                'mode': 2,
                'ts': self.ts
            })

        async with self.session.get(query) as response:
            resp_json: dict = await response.json()
            self.ts = resp_json['ts']
            raw_updates = resp_json['updates']

        return json.dumps(resp_json)
