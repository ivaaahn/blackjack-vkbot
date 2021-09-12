import typing

from app.base.base_game_accessor import BaseGameAccessor
from app.game.game import GameCtx
from app.game.states import BJStates
from app.store.vk_api.dataclasses import Update

if typing.TYPE_CHECKING:
    from app.web.app import Application
    from app.store.vk_api.accessor import VkApiAccessor


class BotManager:
    def __init__(self, app: "Application") -> None:
        self.app = app

    @property
    def vk_api(self) -> "VkApiAccessor":
        return self.app.store.vk_api

    @property
    def game_accessor(self) -> BaseGameAccessor:
        return self.app.store.game

    async def handle_updates(self, updates: list[Update]) -> None:
        import app.game.handlers  # DO NOT DELETE
        for update in updates:
            if update.type == 'message_new':
                msg = update.object.message
                game_ctx = GameCtx(self.game_accessor, msg.peer_id)

                async with game_ctx.proxy() as ctx:
                    if ctx.state is None:
                        ctx.state = BJStates.WAITING_FOR_TRIGGER

                    await ctx.state.handler(self.vk_api, ctx, msg)


def setup(app: "Application") -> None:
    app.bot_manager = BotManager(app)
