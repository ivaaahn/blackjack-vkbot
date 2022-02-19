from proj.store.vk.keyboards import Keyboards
from .base import BotView
from ..misc import get_payload, Choices
from ..states import States

START_MSG = "/go"

__all__ = (
    "TriggerReceivedView",
    "StartActionClickedView",
    "PlayersAmountClickedView",
    "RegistrationClicked",
    "BetReceived",
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
        self.logger.debug(f"{self.button_payload}")

        if not self.button_payload:
            return

        choose = {
            "new_game": lambda: self.interact.handle_new_game(self.ctx),
            "bonus": lambda: self.interact.handle_bonus(self.ctx),
            "balance": lambda: self.interact.handle_balance(self.ctx),
            "stat": lambda: self.interact.handle_statistic(self.ctx),
            "pers_stat": lambda: self.interact.handle_pers_statistic(self.ctx),
            "cancel": lambda: self.interact.do_cancel(self.ctx),
        }

        await choose[self.button_payload]()


class PlayersAmountClickedView(BotView):
    async def execute(self):
        if not self.button_payload:
            return

        if self.button_payload == "cancel":
            await self.interact.do_cancel(self.ctx)
            return

        if self.button_payload not in "123":
            return

        await self.interact.hide_keyboard(self.ctx, f"Количество игроков: {self.button_payload}")
        await self.interact.init_game(self.ctx, int(self.button_payload))

        answer = (
            "Отлично! Чтобы зарегистрироваться на игру, желающие должны нажать кнопку:"
        )
        await self.send(answer, Keyboards.CONFIRM)

        self.ctx.state = States.WAITING_FOR_REGISTRATION


class RegistrationClicked(BotView):
    async def execute(self) -> None:
        if not self.button_payload:
            return

        if self.button_payload == "cancel":
            await self.interact.do_cancel(self.ctx)
            return

        if self.button_payload != "register":
            return

        await self.interact.player_in_game(self.ctx)

        if self.game.all_players_registered:
            await self.interact.complete_registration(self.ctx)
            self.ctx.state = States.WAITING_FOR_BETS


class BetReceived(BotView):
    async def execute(self) -> None:
        if (player := self.game.get_player_by_id(self.ctx.msg.from_id)) is None:
            return

        if self.button_payload == "get out":
            await self.send(f"{player}, вы покидаете игру")
            self.game.drop_player(player)
            if not self.game.players:
                await self.interact.do_cancel(self.ctx)
                return
        else:
            await self.interact.place_bet(self.ctx, player)

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
            "again": lambda: self.interact.repeat_game  (self.ctx),
        }

        try:
            await actions[self.button_payload]()
        except KeyError:
            self.logger.error("Bad payload")
