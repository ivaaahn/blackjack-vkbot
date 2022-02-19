from datetime import timedelta as td

from proj.api.players.models import PlayerModel, PlayerStats
from proj.store import CoreStore
from proj.store.base.accessor import Accessor

from proj.store.vk.dataclasses import Message
from proj.store.vk.keyboards import Keyboard, Keyboards

from ..states import States
from ..context import FSMGameCtxProxy

from ..misc import pretty_time_delta, Choices, parse_bet_expr
from ..game import (
    BlackJackGame,
    Player,
)


__all__ = ("GameInteractionAccessor",)


class GameInteractionAccessor(Accessor[CoreStore, None]):
    def __init__(self, store: CoreStore, **kwargs):
        super().__init__(store, **kwargs)

    async def send(
        self,
        ctx: FSMGameCtxProxy,
        txt: str,
        kbd: Keyboard = Keyboards.EMPTY,
        photos: str = "",
    ):
        await self.store.vk.send_message(
            Message(peer_id=ctx.msg.peer_id, text=txt, kbd=kbd, photos=photos)
        )

    async def handle_new_game(self, ctx: FSMGameCtxProxy) -> None:
        answer = "Выберите количество игроков"
        await self.send(ctx, answer, Keyboards.NUMBER_OF_PLAYERS)

        ctx.state = States.WAITING_FOR_PLAYERS_AMOUNT

    async def handle_balance(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)

        created, player = await self.fetch_user_info(ctx, sets.start_cash)

        answer = f"Баланс твоего счета: {player.cash} у.е."
        await self.send(ctx, answer, Keyboards.START)

        ctx.state = States.WAITING_FOR_START_CHOICE

    async def handle_statistic(self, ctx: FSMGameCtxProxy) -> None:
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

        await self.send(ctx, text, Keyboards.START)

        ctx.state = States.WAITING_FOR_START_CHOICE

    async def personal_player_statistic(
        self, ctx: FSMGameCtxProxy, p: PlayerModel
    ) -> str:

        pos = await self.store.players.get_player_position(ctx.chat_id, p.cash, "cash")

        return f"""
            Статистика для [id{p.vk_id}|{p.first_name} {p.last_name}]%0A%0A%0A
            Позиция в рейтинге: {pos}%0A%0A
            {p.stats}
            """

    async def handle_pers_statistic(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)
        created, player = await self.fetch_user_info(ctx, sets.start_cash)

        await self.send(
            ctx,
            txt=await self.personal_player_statistic(ctx, player),
            kbd=Keyboards.START,
        )

        ctx.state = States.WAITING_FOR_START_CHOICE

    async def handle_bonus(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)
        created, player = await self.fetch_user_info(ctx, sets.start_cash)

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

        await self.send(ctx, answer, Keyboards.START)

    async def fetch_user_info(
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

    async def complete_registration(self, ctx: FSMGameCtxProxy) -> None:
        answer = f"""
            Все игроки зарегистрированы. %0A
            Укажите сумму ставки без пробелов.%0A%0A
            Правила ставок:%0A{ctx.game.min_max_bet_info}%0A
            Ваши счета: %0A{ctx.game.players_cashes_info}
            """

        await self.send(ctx, answer, Keyboards.GET_OUT)

        ctx.state = States.WAITING_FOR_BETS

    async def complete_betting(self, ctx: FSMGameCtxProxy) -> None:
        answer = "Все игроки поставили ставки! Начинаю раздачу карт..."
        await self.send(ctx, answer, Keyboards.EMPTY)

    async def hand_out_cards(self, ctx: FSMGameCtxProxy) -> None:
        g = ctx.game
        # TODO get_card

        try:
            g.deal_cards()
        except IndexError as e:
            await self.do_end(ctx)
            await self.send(
                ctx,
                txt="Колода закончилась! Данная игра не может быть продолжена",
                kbd=Keyboards.START,
            )
            ctx.state = States.WAITING_FOR_START_CHOICE
        else:
            await self.send(
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

    async def bj_ask_player(self, ctx: FSMGameCtxProxy) -> None:
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

        await self.send(ctx, answer, kbd=kbd)

    async def ask_player(self, ctx: FSMGameCtxProxy):
        curr_player = ctx.game.current_player

        if curr_player.has_blackjack:
            await self.bj_ask_player(ctx)
        else:
            await self.base_ask_player(ctx)

    async def base_ask_player(self, ctx: FSMGameCtxProxy):
        player, dealer = ctx.game.current_player, ctx.game.dealer
        answer = f"{player}, Сумма очков: {player.score} ({dealer}: {dealer.score})"
        await self.send(ctx, answer, kbd=Keyboards.CHOOSE_ACTION)

    async def handle_bj_pick_up11_action(
        self, ctx: FSMGameCtxProxy, player: Player
    ) -> bool:
        player.set_bj_win11_status()
        answer = f"{player}%0A, забирай 1:1!"
        await self.send(ctx, answer)
        return True

    async def handle_bj_pick_up32_action(self, _: FSMGameCtxProxy, __: Player) -> bool:
        return True

    async def handle_bj_wait_action(self, ctx: FSMGameCtxProxy, player: Player) -> bool:
        player.set_bj_waiting_for_end_status()
        answer = f"{player}, ожидай конца игры!"
        await self.send(ctx, answer)
        return True

    async def handle_hit_action(self, ctx: FSMGameCtxProxy, player: Player) -> bool:
        # TODO get_card
        try:
            player.add_card(ctx.game.deck.get_card())
        except IndexError as e:
            await self.do_end(ctx)
            await self.send(
                ctx,
                "Колода закончилась! Данная игра не может быть продолжена",
                Keyboards.START,
            )
            ctx.state = States.WAITING_FOR_START_CHOICE
        else:
            answer = f"{player}%0A{player.cards_info}"
            await self.send(ctx, answer)
            return player.not_bust

    async def handle_player_bust(self, ctx: FSMGameCtxProxy, player: Player) -> bool:
        player.set_bust_status()
        answer = f"{player}, много! (Сумма: {player.score})"
        await self.send(ctx, answer)
        return True

    async def handle_stand_action(self, _: FSMGameCtxProxy, __: Player) -> bool:
        return True

    async def dispatch(
        self,
        ctx: FSMGameCtxProxy,
        player: Player,
        choice: Choices,
        action_res: bool,
    ) -> None:
        if choice is Choices.HIT and action_res and player.score != 21:
            await self.base_ask_player(ctx)
            return

        if choice is Choices.HIT and not action_res:
            await self.handle_player_bust(ctx, player)

        if ctx.game.next_player():
            await self.ask_player(ctx)
        else:
            # TODO get_card

            try:
                ctx.game.handle_dealer()
            except IndexError as e:
                await self.do_end(ctx)
                await self.send(
                    ctx,
                    "Колода закончилась! Данная игра не может быть продолжена",
                    Keyboards.START,
                )
                ctx.state = States.WAITING_FOR_START_CHOICE
            else:
                await self.handle_results(ctx)
                await self.show_results(ctx)
                await self.update_players_data(ctx)
                ctx.state = States.WAITING_FOR_LAST_CHOICE

    async def handle_results(self, ctx: FSMGameCtxProxy):
        ctx.game.define_results()

    async def show_results(self, ctx: FSMGameCtxProxy):
        game = ctx.game
        d = game.dealer
        answer = f"◾ {d}%0A{d.cards_info}%0A%0AСумма очков: {d.score}"
        if d.has_blackjack:
            answer += "(Блэк-джек)"
        await self.send(ctx, answer)

        answer = f"""
        Результаты игры:%0A
        {'%0A'.join([f'🔺 {p} - {p.status.value} (Счет: {p.cash})' for p in game.players])} 
        """
        await self.send(ctx, answer, Keyboards.REPEAT_GAME_QUESTION)

    async def init_game(self, ctx: FSMGameCtxProxy, num_of_players: int) -> None:
        sets = await self.store.game_settings.get(_id=0)
        ctx.game = BlackJackGame(
            chat_id=ctx.msg.peer_id,
            players_qty=num_of_players,
            min_bet=sets.min_bet,
            max_bet=sets.max_bet,
            decks_qty=sets.num_of_decks,
        )

    async def player_in_game(self, ctx: FSMGameCtxProxy) -> None:
        sets = await self.store.game_settings.get(_id=0)
        _, db_player_data = await self.fetch_user_info(ctx, sets.start_cash)
        new_player = Player(
            name=db_player_data.first_name,
            vk_id=db_player_data.vk_id,
            cash=db_player_data.cash,
        )

        if ctx.game.add_player(new_player):
            answer = f"{new_player}, ты в игре! (Зарегистрировано: {ctx.game.ratio_of_registered})"
        else:
            answer = f"{new_player}, ты уже в игре. Дождись остальных игроков!"

        await self.send(ctx, answer, Keyboards.CONFIRM)

    async def place_bet(self, ctx: FSMGameCtxProxy, player: Player) -> None:
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

        await self.send(ctx, answer, Keyboards.GET_OUT)

    async def repeat_game(self, ctx: FSMGameCtxProxy) -> None:
        answer = f"""Круто, играем снова! Укажите сумму ставки без пробелов.%0A%0A
                Ваши счета: %0A{ctx.game.players_cashes_info}
            """

        await self.send(ctx, answer, Keyboards.GET_OUT)

        ctx.game.reset()
        ctx.state = States.WAITING_FOR_BETS

    async def end_game(self, ctx: FSMGameCtxProxy) -> None:
        answer = f"Окей, больше не играем!"
        await self.send(ctx, answer)
        await self.do_end(ctx)

    async def calculate_stats(
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

    async def update_players_data(self, ctx: FSMGameCtxProxy) -> None:
        for player in ctx.game.players:
            new_stats = await self.calculate_stats(ctx, player)
            await self.store.players.update_after_game(
                ctx.chat_id, player.vk_id, player.cash, new_stats
            )

    async def do_force_cancel(self, ctx: FSMGameCtxProxy) -> None:
        await self.hide_keyboard(ctx, "Ой, что-то пошло не так :(")
        await self.do_end(ctx)

    async def do_cancel(self, ctx: FSMGameCtxProxy) -> None:
        await self.hide_keyboard(ctx, "Отмена игры")
        await self.do_end(ctx)

    async def do_end(self, ctx: FSMGameCtxProxy) -> None:
        del ctx.state
        del ctx.game

    async def hide_keyboard(self, ctx: FSMGameCtxProxy, text: str) -> None:
        await self.send(ctx, text)
