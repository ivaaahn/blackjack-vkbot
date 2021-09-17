from app.base.base_game_accessor import BaseGameAccessor
from app.game.game import GameCtx
from app.game.states import BJStates
from app.store import PlayersAccessor
from app.store.vk_api.dataclasses import Update
from app.game.dataclasses import GAccessors
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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

    @property
    def player_accessor(self) -> PlayersAccessor:
        return self.app.store.players

    async def handle_updates(self, updates: list[Update]) -> None:
        import app.game.handlers  # DO NOT DELETE
        for update in updates:
            if update.type == 'message_new':
                msg = update.object.message
                game_ctx = GameCtx(self.game_accessor, msg.peer_id, msg)
                game_accessors = GAccessors(self.vk_api, self.player_accessor)

                async with game_ctx.proxy() as ctx:
                    if ctx.state is None:
                        ctx.state = BJStates.WAITING_FOR_TRIGGER

                    await ctx.state.handler(ctx, game_accessors)


def setup(app: "Application") -> None:
    app.bot_manager = BotManager(app)
