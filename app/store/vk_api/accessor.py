import random
import typing
from pprint import pprint
from typing import Optional

import aiohttp
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import Message, Update, UpdateObject, UpdateMessage, User
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.app import Application
    from app.config import BotConfig


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        super().__init__(app)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    @property
    def cfg(self) -> "BotConfig":
        return self.app.config.bot

    async def connect(self, app: "Application"):
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        self.poller = Poller(self.app.store, self.app.bot_manager)
        await self._get_long_poll_service()
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session is not None:
            await self.session.close()
            self.session = None

        if self.poller is not None and self.poller.is_running:
            await self.poller.stop()
            self.poller = None

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"

        url += '&'.join(
            f'{k}={v if not isinstance(v, list) else ",".join(tuple(map(str, v)))}' for k, v in params.items())

        return url

    async def _get_long_poll_service(self):
        group_id = self.app.config.bot.group_id
        token = self.app.config.bot.token

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

    async def poll(self) -> list[Update]:
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

        return self._pack_updates(raw_updates)

    async def send_message(self, message: Message) -> None:
        query_params = {
            'message': message.text,
            'access_token': self.app.config.bot.token,
            'random_id': random.randint(-2147483648, 2147483648),
            'peer_id': message.peer_id,
            'keyboard': message.kbd.serialize(),
            'attachment': message.photos,
        }

        query = self._build_query(
            host='https://api.vk.com/',
            method='method/messages.send',
            params=query_params
        )

        # pprint(f'{query=}')

        async with self.session.get(query) as resp:
            resp = await resp.json()
            # pprint(f'{resp=}')

    async def get_chat(self, peer_id: int) -> dict:
        query = self._build_query(
            host='https://api.vk.com/',
            method='method/messages.getConversationMembers',
            params={
                'access_token': self.cfg.token,
                'peer_id': peer_id,
            }
        )

        async with self.session.get(query) as resp:
            return await resp.json()

    async def get_users(self, vk_ids: list[int]) -> list[User]:
        query = self._build_query(
            host='https://api.vk.com/',
            method='method/users.get',
            params={
                'access_token': self.cfg.token,
                'user_ids': vk_ids,
                'fields': [
                    'bdate',
                    'city',
                ]
            }
        )

        async with self.session.get(query) as resp:
            data = await resp.json()

        return [User.from_dict(u) for u in data['response']]

    @staticmethod
    def _pack_updates(raw_updates: dict) -> list[Update]:
        return [
            Update(
                type=u['type'],
                object=UpdateObject(
                    message=UpdateMessage(
                        from_id=u['object']['message']['from_id'],
                        text=u['object']['message']['text'],
                        id=u['object']['message']['id'],
                        peer_id=u['object']['message']['peer_id'],
                        payload=u['object']['message'].get('payload')
                    ))) for u in raw_updates if u['type'] == 'message_new']
