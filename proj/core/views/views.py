from proj.store.vk.keyboards import Keyboards
from .base import BotView
from ..misc import get_payload, Choices
from ..states import States

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
        if START_MSG not in self.ctx.msg.text:
            return

        answer = "Привет, меня зовут BlackjackBot!"
        await self.send(answer, Keyboards.START)

        self.ctx.state = States.WAITING_FOR_START_CHOICE


class StartActionClickedView(BotView):
    async def execute(self):
        if self.button_payload:
            await self.interact.handle_start_action(self.button_payload, self.ctx)


class PlayersAmountClickedView(BotView):
    async def execute(self):
        if self.button_payload:
            await self.interact.handle_receiving_players_amount(
                self.button_payload, self.ctx
            )


class RegistrationClickedView(BotView):
    async def execute(self) -> None:
        if self.button_payload == "register":
            await self.interact.handle_player_registration(self.ctx)


class BetReceivedView(BotView):
    async def execute(self) -> None:
        curr_player = self.game.get_player_by_id(
            vk_id=self.ctx.msg.from_id
        )

        if not curr_player:
            return

        if self.button_payload == "get out":
            await self.send(f"{curr_player}, вы покидаете игру")
            self.game.drop_player(curr_player)

            if not self.game.players:
                await self.interact._do_cancel(self.ctx)
                return
        else:
            await self.interact.place_bet(self.ctx, curr_player)

        if self.game.all_players_bet:
            await self.interact.hand_out_cards(self.ctx)
            await self.interact.ask_player(self.ctx)
            self.ctx.state = States.WAITING_FOR_ACTION


class ActionClicked(BotView):
    async def execute(self) -> None:
        player = self.game.current_player

        if self.ctx.msg.from_id != player.vk_id:
            return

        actions = {
            Choices.HIT: lambda: self.interact.handle_hit_action(self.ctx, player),
            Choices.STAND: lambda: self.interact.handle_stand_action(self.ctx, player),
            Choices.BJ_WAIT: lambda: self.interact.handle_bj_wait_action(
                self.ctx, player
            ),
            Choices.BJ_PICK_UP11: lambda: self.interact.handle_bj_pick_up11_action(
                self.ctx, player
            ),
            Choices.BJ_PICK_UP32: lambda: self.interact.handle_bj_pick_up32_action(
                self.ctx, player
            ),
        }

        try:
            choice = Choices(self.button_payload)
        except ValueError:
            return

        res = await actions[choice]()

        await self.interact.dispatch(self.ctx, player, choice, res)


class LastActionClicked(BotView):
    async def execute(self) -> None:
        if not self.button_payload:
            return

        if self.ctx.msg.from_id not in self.game.players_ids:
            return

        actions = {
            "stop": lambda: self.interact.end_game(self.ctx),
            "again": lambda: self.interact.repeat_game(self.ctx),
        }

        try:
            await actions[self.button_payload]()
        except KeyError:
            self.logger.error("Bad payload")
