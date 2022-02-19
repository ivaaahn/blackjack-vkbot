from .base import BotView

START_MSG = "/go"

__all__ = (
    "TriggerReceivedView",
    "StartActionClickedView",
    "PlayersAmountClickedView",
    "RegistrationClickedView",
    "BetReceivedView",
    "ActionClicked",
    "LastActionClicked",
)


class TriggerReceivedView(BotView):
    async def execute(self):
        if START_MSG in self.ctx.msg.text:
            await self.interact.handle_trigger(self.ctx)


class StartActionClickedView(BotView):
    async def execute(self):
        if self.payload_btn:
            await self.interact.handle_start_action(self.payload_btn, self.ctx)


class PlayersAmountClickedView(BotView):
    async def execute(self):
        if self.payload_btn:
            await self.interact._handle_receiving_players_amount(
                self.payload_btn, self.ctx
            )


class RegistrationClickedView(BotView):
    async def execute(self) -> None:
        if self.payload_btn == "register":
            await self.interact.handle_player_registration(self.ctx)


class BetReceivedView(BotView):
    async def execute(self) -> None:
        await self.interact.handle_betting(self.payload_btn, self.ctx)


class ActionClicked(BotView):
    async def execute(self) -> None:
        if self.ctx.msg.from_id == self.game.current_player.vk_id:
            await self.interact.handle_main_action(self.ctx, self.payload_btn)


class LastActionClicked(BotView):
    async def execute(self) -> None:
        if self.payload_btn and self.ctx.msg.from_id in self.game.players_ids:
            await self.interact.handle_last_action(self.ctx, self.payload_btn)
