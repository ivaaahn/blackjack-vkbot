from datetime import timedelta as td

from proj.api.players.models import PlayerModel, PlayerStats
from proj.store import CoreStore
from proj.store.base.accessor import Accessor

from proj.store.vk.dataclasses import Message
from proj.store.vk.keyboards import Keyboard, Keyboards

from ..states import States
from ..context import FSMGameCtxProxy

from ..misc import pretty_time_delta, parse_bet_expr
from ..types import MainActionChoiceType, StartActionChoiceType, LastActionChoiceType
from ..game import (
    BlackJackGame,
    Player,
)


__all__ = ("GameInteractionAccessor",)

from ..views.base import ContextProxy


class GameInteractionAccessor(Accessor[CoreStore, None]):
    def __init__(self, store: CoreStore, **kwargs):
        super().__init__(store, **kwargs)

        self._start_actions_matching = {
            StartActionChoiceType.new_game: self._handle_new_game,
            StartActionChoiceType.get_bonus: self._handle_bonus,
            StartActionChoiceType.show_balance: self._handle_balance,
            StartActionChoiceType.common_statistic: self._handle_statistic,
            StartActionChoiceType.personal_statistic: self._handle_pers_statistic,
            StartActionChoiceType.cancel: self._do_cancel,
        }

        self._main_actions_matching = {
            MainActionChoiceType.hit: self._handle_hit_action,
            MainActionChoiceType.stand: self._handle_stand_action,
            MainActionChoiceType.blackjack_wait_for: self._handle_bj_wait_action,
            MainActionChoiceType.blackjack_pickup11: self.handle_bj_pick_up11_action,
            MainActionChoiceType.blackjack_pickup32: self._handle_bj_pick_up32_action,
        }

        self._last_actions_matching = {
            LastActionChoiceType.end_game: self._end_game,
            LastActionChoiceType.repeat_game: self._repeat_game,
        }

    async def handle_trigger(self, context: FSMGameCtxProxy):
        answer = "Привет, меня зовут BlackjackBot!"
        await self._send(context, answer, Keyboards.START)

        context.state = States.WAITING_FOR_START_CHOICE

    async def handle_start_action(self, payload: str, context: FSMGameCtxProxy):
        action_handler = self._start_actions_matching[StartActionChoiceType(payload)]
        await action_handler(context)

    async def handle_player_registration(self, context: FSMGameCtxProxy):
        await self._add_player_in_game(context)

        if context.game.all_players_registered:
            await self._complete_registration(context)
            context.state = States.WAITING_FOR_BETS

    async def handle_betting(self, payload: str, context: FSMGameCtxProxy):
        curr_player = context.game.get_player_by_id(vk_id=context.msg.from_id)

        if not curr_player:
            return

        if payload == "leaving the game":
            await self._leaving_game_instead_of_betting(context, curr_player)
            return

        await self._place_bet(context, curr_player)
        await self._handle_betting_completion(context)

    async def handle_main_action(self, context: FSMGameCtxProxy, payload: str):
        try:
            choice = MainActionChoiceType(payload)
        except ValueError:
            return

        action_handler = self._main_actions_matching[choice]

        curr_player = context.game.current_player
        res = await action_handler(context, curr_player)  # TODO WTF

        await self._dispatch(context, curr_player, choice, res)

    async def handle_last_action(self, context: FSMGameCtxProxy, payload: str):
        action_handler = self._last_actions_matching[LastActionChoiceType(payload)]
        await action_handler(context)

    async def _send(
        self,
        ctx: FSMGameCtxProxy,
        txt: str,
        kbd: Keyboard = Keyboards.EMPTY,
        photos: str = "",
    ):
        await self.store.vk.send_message(
            Message(peer_id=ctx.msg.peer_id, text=txt, kbd=kbd, photos=photos)
        )

    async def _handle_receiving_players_amount(
        self, choice: str, context: FSMGameCtxProxy
    ):
        if choice not in "123":
            return

        await self._hide_keyboard(context, f"Количество игроков: {choice}")
        await self._init_game(context, int(choice))

        answer = (
            "Отлично! Чтобы зарегистрироваться на игру, желающие должны нажать кнопку:"
        )
        await self._send(context, answer, Keyboards.CONFIRM)

        context.state = States.WAITING_FOR_REGISTRATION

    async def _handle_new_game(self, ctx: FSMGameCtxProxy) -> None:
        answer = "Выберите количество игроков"
        await self._send(ctx, answer, Keyboards.NUMBER_OF_PLAYERS)

        ctx.state = States.WAITING_FOR_PLAYERS_AMOUNT

    async def _handle_balance(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)

        created, player = await self._fetch_user_info(ctx, sets.start_cash)

        answer = f"Баланс твоего счета: {player.cash} у.е."
        await self._send(ctx, answer, Keyboards.START)

        ctx.state = States.WAITING_FOR_START_CHOICE

    async def _handle_statistic(self, ctx: FSMGameCtxProxy) -> None:
        limit, offset = 10, 0
        order_by, order_type = "cash", -1

        players = await self.store.players.get_players_list(
            vk_id=None,
            chat_id=ctx.chat_id,
            offset=offset,
            limit=limit,
            order_by=order_by,
            order_type=order_type,
        )

        text = "Топ 10 игроков чата:%0A%0A"
        text += "%0A".join(f"{idx + 1}) {p}" for idx, p in enumerate(players))

        await self._send(ctx, text, Keyboards.START)

        ctx.state = States.WAITING_FOR_START_CHOICE

    async def _handle_betting_completion(self, context: FSMGameCtxProxy):
        if context.game.all_players_bet:
            await self._hand_out_cards(context)
            await self._ask_player(context)
            context.state = States.WAITING_FOR_ACTION

    async def _leaving_game_instead_of_betting(
        self, context: FSMGameCtxProxy, curr_player: Player
    ):
        await self._send(context, f"{curr_player}, вы покидаете игру")
        context.game.drop_player(curr_player)

        if context.game.players:
            await self._handle_betting_completion(context)
        else:
            await self._do_cancel(context)

    async def _personal_player_statistic(
        self, ctx: FSMGameCtxProxy, p: PlayerModel
    ) -> str:

        pos = await self.store.players.get_player_position(ctx.chat_id, p.cash, "cash")

        return f"""
            Статистика для [id{p.vk_id}|{p.first_name} {p.last_name}]%0A%0A%0A
            Позиция в рейтинге: {pos}%0A%0A
            {p.stats}
            """

    async def _handle_pers_statistic(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)
        created, player = await self._fetch_user_info(ctx, sets.start_cash)

        await self._send(
            ctx,
            txt=await self._personal_player_statistic(ctx, player),
            kbd=Keyboards.START,
        )

        ctx.state = States.WAITING_FOR_START_CHOICE

    async def _handle_bonus(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)
        created, player = await self._fetch_user_info(ctx, sets.start_cash)

        if created:
            answer = f"""А вы у нас впервые, поэтому мы Вам начисляем {sets.start_cash}$%0A
            Следующий бонус будет доступен через {pretty_time_delta(td(minutes=sets.bonus_period))}"""
        elif player.check_bonus(sets.bonus_period):
            answer = f"""Вы получаете ежедневный бонус: {sets.bonus}$%0A
            Следующий бонус будет доступен через {pretty_time_delta(td(minutes=sets.bonus_period))}"""
            await self.store.players.give_bonus(
                ctx.chat_id, player.vk_id, player.cash + sets.bonus
            )
        else:
            answer = f"""К сожалению бонус еще не доступен :(%0A
            Ближайший бонус будет доступен через {pretty_time_delta(player.td_to_bonus(sets.bonus_period))}"""

        await self._send(ctx, answer, Keyboards.START)

    async def _fetch_user_info(
        self, ctx: FSMGameCtxProxy, start_cash: float
    ) -> tuple[bool, PlayerModel]:
        """
        :return: (flag, PlayerModel). Flag is True if new players was created
        """

        flag = False
        db_user_data = await self.store.players.get_player_by_vk_id(
            chat_id=ctx.chat_id, vk_id=ctx.msg.from_id
        )
        if db_user_data is None:
            flag = True
            vk_user_data = (await self.store.vk.get_users([ctx.msg.from_id]))[0]
            await self.store.players.add_player(
                vk_id=vk_user_data.vk_id,
                chat_id=ctx.chat_id,
                first_name=vk_user_data.first_name,
                last_name=vk_user_data.last_name,
                birthday=vk_user_data.birthday,
                city=vk_user_data.city,
                start_cash=start_cash,
            )

        return flag, await self.store.players.get_player_by_vk_id(
            chat_id=ctx.chat_id, vk_id=ctx.msg.from_id
        )

    async def _complete_registration(self, ctx: FSMGameCtxProxy) -> None:
        answer = f"""
            Все игроки зарегистрированы. %0A
            Укажите сумму ставки без пробелов.%0A%0A
            Правила ставок:%0A{ctx.game.min_max_bet_info}%0A
            Ваши счета: %0A{ctx.game.players_cashes_info}
            """

        await self._send(ctx, answer, Keyboards.GET_OUT)

        ctx.state = States.WAITING_FOR_BETS

    async def _complete_betting(self, ctx: FSMGameCtxProxy) -> None:
        answer = "Все игроки поставили ставки! Начинаю раздачу карт..."
        await self._send(ctx, answer, Keyboards.EMPTY)

    async def _hand_out_cards(self, ctx: FSMGameCtxProxy) -> None:
        g = ctx.game
        # TODO get_card

        try:
            g.deal_cards()
        except IndexError as e:
            await self._do_end(ctx)
            await self._send(
                ctx,
                txt="Колода закончилась! Данная игра не может быть продолжена",
                kbd=Keyboards.START,
            )
            ctx.state = States.WAITING_FOR_START_CHOICE
        else:
            await self._send(
                ctx,
                txt=(
                    f"%0A%0A".join(
                        [
                            f"◾ {p}, вот твои карты:%0A{p.cards_info}"
                            for p in g.players_and_dealer
                        ]
                    )
                ),
            )

        # for player in ctx.game.players_and_dealer:
        #     await send(ctx, f'{player}%0A{player.cards}')
        # await send(ctx, f'{player}', photos=player.cards_photos)

    async def _bj_ask_player(self, ctx: FSMGameCtxProxy) -> None:
        player, dealer = ctx.game.current_player, ctx.game.dealer

        ctx.game.handle_player_blackjack(player)

        answer = f"{player}, У тебя блэкджек!%0A"

        if player.status_is_bj_need_to_clarify:
            answer += "Выбирай"
            kbd = Keyboards.BJ_DEALER_WITH_ACE
        elif player.status_is_bj_win32:
            answer += f"Поздравляем с победой!"
            kbd = Keyboards.BJ_WIN_32
        else:
            answer += "Жди конца игры"
            kbd = Keyboards.BJ_DEALER_WITHOUT_ACE

        await self._send(ctx, answer, kbd=kbd)

    async def _ask_player(self, ctx: FSMGameCtxProxy):
        curr_player = ctx.game.current_player

        if curr_player.has_blackjack:
            await self._bj_ask_player(ctx)
        else:
            await self._base_ask_player(ctx)

    async def _base_ask_player(self, ctx: FSMGameCtxProxy):
        player, dealer = ctx.game.current_player, ctx.game.dealer
        answer = f"{player}, Сумма очков: {player.score} ({dealer}: {dealer.score})"
        await self._send(ctx, answer, kbd=Keyboards.CHOOSE_ACTION)

    async def handle_bj_pick_up11_action(
        self, ctx: FSMGameCtxProxy, player: Player
    ) -> bool:
        player.set_bj_win11_status()
        answer = f"{player}%0A, забирай 1:1!"
        await self._send(ctx, answer)
        return True

    @staticmethod
    async def _handle_bj_pick_up32_action(_: FSMGameCtxProxy, __: Player) -> bool:
        return True

    async def _handle_bj_wait_action(
        self, ctx: FSMGameCtxProxy, player: Player
    ) -> bool:
        player.set_bj_waiting_for_end_status()
        answer = f"{player}, ожидай конца игры!"
        await self._send(ctx, answer)
        return True

    async def _handle_hit_action(self, ctx: FSMGameCtxProxy, player: Player) -> bool:
        # TODO get_card
        try:
            player.add_card(ctx.game.deck.get_card())
        except IndexError as e:
            await self._do_end(ctx)
            await self._send(
                ctx,
                "Колода закончилась! Данная игра не может быть продолжена",
                Keyboards.START,
            )
            ctx.state = States.WAITING_FOR_START_CHOICE
        else:
            answer = f"{player}%0A{player.cards_info}"
            await self._send(ctx, answer)
            return player.not_bust

    async def _handle_player_bust(self, ctx: FSMGameCtxProxy, player: Player) -> bool:
        player.set_bust_status()
        answer = f"{player}, много! (Сумма: {player.score})"
        await self._send(ctx, answer)
        return True

    @staticmethod
    async def _handle_stand_action(_: FSMGameCtxProxy, __: Player) -> bool:
        return True

    async def _dispatch(
        self,
        ctx: FSMGameCtxProxy,
        player: Player,
        choice: MainActionChoiceType,
        action_res: bool,
    ) -> None:
        if choice is MainActionChoiceType.hit and action_res and player.score != 21:
            await self._base_ask_player(ctx)
            return

        if choice is MainActionChoiceType.hit and not action_res:
            await self._handle_player_bust(ctx, player)

        if ctx.game.next_player():
            await self._ask_player(ctx)
        else:
            # TODO get_card

            try:
                ctx.game.handle_dealer()
            except IndexError as e:
                await self._do_end(ctx)
                await self._send(
                    ctx,
                    "Колода закончилась! Данная игра не может быть продолжена",
                    Keyboards.START,
                )
                ctx.state = States.WAITING_FOR_START_CHOICE
            else:
                await self._handle_results(ctx)
                await self._show_results(ctx)
                await self._update_players_data(ctx)
                ctx.state = States.WAITING_FOR_LAST_CHOICE

    @staticmethod
    async def _handle_results(ctx: FSMGameCtxProxy):
        ctx.game.define_results()

    async def _show_results(self, ctx: FSMGameCtxProxy):
        game = ctx.game
        d = game.dealer
        answer = f"◾ {d}%0A{d.cards_info}%0A%0AСумма очков: {d.score}"
        if d.has_blackjack:
            answer += "(Блэк-джек)"
        await self._send(ctx, answer)

        answer = f"""
        Результаты игры:%0A
        {'%0A'.join([f'🔺 {p} - {p.status.value} (Счет: {p.cash})' for p in game.players])} 
        """
        await self._send(ctx, answer, Keyboards.REPEAT_GAME_QUESTION)

    async def _init_game(self, ctx: FSMGameCtxProxy, num_of_players: int) -> None:
        sets = await self.store.game_settings.get(_id=0)
        ctx.game = BlackJackGame(
            chat_id=ctx.msg.peer_id,
            players_qty=num_of_players,
            min_bet=sets.min_bet,
            max_bet=sets.max_bet,
            decks_qty=sets.num_of_decks,
        )

    async def _add_player_in_game(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)
        _, db_player_data = await self._fetch_user_info(ctx, sets.start_cash)
        new_player = Player(
            name=db_player_data.first_name,
            vk_id=db_player_data.vk_id,
            cash=db_player_data.cash,
        )

        if ctx.game.add_player(new_player):
            answer = f"{new_player}, ты в игре! (Зарегистрировано: {ctx.game.ratio_of_registered})"
        else:
            answer = f"{new_player}, ты уже в игре. Дождись остальных игроков!"

        await self._send(ctx, answer, Keyboards.CONFIRM)

    async def _place_bet(self, ctx: FSMGameCtxProxy, player: Player) -> None:
        if (bet := parse_bet_expr(ctx.msg.text)) is None or bet < 0:
            answer = f"{player}, вы указали некорректную сумму ставки"
        elif bet > player.cash:
            answer = f"{player}, на счете недостаточно денег, дружище. На счете: {player.cash}"
        elif bet > ctx.game.max_bet:
            answer = f"{player}, ты превысил максимальную ставку стола%0A{ctx.game.min_max_bet_info}"
        elif bet < ctx.game.min_bet:
            answer = f"{player}, твоя ставка ниже минимальной ставки стола%0A{ctx.game.min_max_bet_info}"
        else:
            answer = f"{player}, ваша ставка принята! Сумма ставки: {bet}"
            player.place_bet(bet)

        await self._send(ctx, answer, Keyboards.GET_OUT)

    async def _repeat_game(self, ctx: FSMGameCtxProxy) -> None:
        answer = f"""Круто, играем снова! Укажите сумму ставки без пробелов.%0A%0A
                Ваши счета: %0A{ctx.game.players_cashes_info}
            """

        await self._send(ctx, answer, Keyboards.GET_OUT)

        ctx.game.reset()
        ctx.state = States.WAITING_FOR_BETS

    async def _end_game(self, ctx: FSMGameCtxProxy) -> None:
        answer = f"Окей, больше не играем!"
        await self._send(ctx, answer)
        await self._do_end(ctx)

    async def _calculate_stats(
        self, ctx: FSMGameCtxProxy, player: Player
    ) -> PlayerStats:
        p = await self.store.players.get_player_by_vk_id(
            chat_id=ctx.chat_id, vk_id=player.vk_id
        )

        st = p.stats
        st.max_cash = max(st.max_cash, player.cash)
        st.number_of_games += 1

        if player.is_winner:
            st.number_of_wins += 1
            st.max_win = (
                player.calc_win()
                if st.max_win is None
                else max(st.max_win, player.calc_win())
            )
        elif player.is_loser:
            st.number_of_defeats += 1

        st.max_bet = player.bet if st.max_bet is None else max(st.max_bet, player.bet)
        st.average_bet = (
            player.bet
            if st.average_bet is None
            else (st.average_bet * (st.number_of_games - 1) + player.bet)
            / st.number_of_games
        )

        return st

    async def _update_players_data(self, ctx: FSMGameCtxProxy) -> None:
        for player in ctx.game.players:
            new_stats = await self._calculate_stats(ctx, player)
            await self.store.players.update_after_game(
                ctx.chat_id, player.vk_id, player.cash, new_stats
            )

    async def _do_force_cancel(self, ctx: FSMGameCtxProxy) -> None:
        await self._hide_keyboard(ctx, "Ой, что-то пошло не так :(")
        await self._do_end(ctx)

    async def _do_cancel(self, ctx: FSMGameCtxProxy) -> None:
        await self._hide_keyboard(ctx, "Отмена игры")
        await self._do_end(ctx)

    @staticmethod
    async def _do_end(ctx: FSMGameCtxProxy) -> None:
        del ctx.state
        del ctx.game

    async def _hide_keyboard(self, ctx: FSMGameCtxProxy, text: str) -> None:
        await self._send(ctx, text)
