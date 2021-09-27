import json
import traceback

from typing import TYPE_CHECKING
from aio_pika import IncomingMessage

from app.game.dataclasses import GAccessors
from app.game.game import GameCtx
from app.game.logic import do_force_cancel
from app.game.states import States
from app.store.vk_api.dataclasses import Update, UpdateObject, UpdateMessage

if TYPE_CHECKING:
    from app.app import Application
    from app.store.players.accessor import PlayersAccessor
    from app.store.vk_api.accessor import VkApiAccessor
    from app.base.base_game_accessor import BaseGameAccessor
    from app.store.game_settings.accessor import GameSettingsAccessor


class BotManager:
    def __init__(self, app: "Application") -> None:
        self.app = app

    @property
    def vk_api(self) -> "VkApiAccessor":
        return self.app.store.vk_api

    @property
    def g_accessor(self) -> "BaseGameAccessor":
        return self.app.store.game

    @property
    def p_accessor(self) -> "PlayersAccessor":
        return self.app.store.players

    @property
    def gs_accessor(self) -> "GameSettingsAccessor":
        return self.app.store.game_settings

    async def handle_rabbit_msg(self, msg: IncomingMessage) -> None:
        async with msg.process():
            updates_json = json.loads(msg.body.decode(encoding='utf-8'))['updates']
            if updates_json:
                await self.handle_updates(self._pack_updates(updates_json))

    async def handle_updates(self, updates: list[Update]) -> None:
        import app.game.handlers  # DO NOT DELETE
        for update in updates:
            msg = update.object.message
            async with GameCtx(self.g_accessor, msg.peer_id, msg).proxy() as ctx:
                if ctx.state is None:
                    ctx.state = States.WAITING_FOR_TRIGGER

                accessors = GAccessors(self.vk_api, self.p_accessor, self.gs_accessor)

                try:
                    await ctx.state.handler(ctx, accessors)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    await do_force_cancel(ctx, accessors)

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


def setup(app: "Application") -> None:
    app.bot_manager = BotManager(app)
