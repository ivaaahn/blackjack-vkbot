from datetime import datetime, timedelta as td
from typing import TYPE_CHECKING

from app.api.players.models import PlayerModel
from app.game.game import GameCtxProxy, BlackJackGame
from app.game.keyboards import Keyboards as Kbds, Keyboard
from app.game.player import Player
from app.game.states import States
from app.game.utils import parse_bet_expr, Choices
from app.store.vk_api.dataclasses import Message

if TYPE_CHECKING:
    from app.game.dataclasses import GAccessors


async def handle_new_game(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = 'Выберите количество игроков'
    await send(ctx, access, answer, kbd=Kbds.NUMBER_OF_PLAYERS)
    ctx.state = States.WAITING_FOR_PLAYERS_AMOUNT


async def handle_balance(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    sets = await access.settings.get(_id=0)
    created, player = await fetch_user_info(ctx, access, sets.start_cash)
    answer = f'Баланс твоего счета: {player.cash} у.е.'
    await send(ctx, access, answer, Kbds.START)
    ctx.state = States.WAITING_FOR_START_CHOICE


async def handle_statistic(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    sets = await access.settings.get(_id=0)
    limit, offset = 10, 0
    order_by, order_type = 'cash', -1

    players = await access.players.get_players_list(
        chat_id=ctx.chat_id,
        offset=offset,
        limit=limit,
        order_by=order_by,
        order_type=order_type
    )

    text = 'Топ 10 игроков чата:%0A%0A'
    text += '%0A'.join(f'{idx + 1}) {p}' for idx, p in enumerate(players))

    await send(ctx, access, text, Kbds.START)
    ctx.state = States.WAITING_FOR_START_CHOICE


async def handle_bonus(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    sets = await access.settings.get(_id=0)
    created, player = await fetch_user_info(ctx, access, sets.start_cash)

    if created:
        answer = f'''А вы у нас впервые, получайте свой бонус: {sets.bonus} у.е.%0A
        Следующий бонус будет доступен {pretty_datetime(td(minutes=sets.bonus_period) + datetime.now())}'''
    elif player.check_bonus(sets.bonus_period):
        answer = f'''Вы получаете ежедневный бонус: {sets.bonus} у.е.%0A
        Следующий бонус будет доступен {pretty_datetime(td(minutes=sets.bonus_period) + datetime.now())}'''
        await access.players.give_bonus(ctx.chat_id, player.vk_id, player.cash + sets.bonus)
    else:
        answer = f'''К сожалению бонус еще не доступен :(%0A
        Ближайший бонус будет доступен {pretty_datetime(td(minutes=sets.bonus_period) + player.last_bonus_date)}'''

    await send(ctx, access, answer, Kbds.START)


async def fetch_user_info(ctx: GameCtxProxy, access: 'GAccessors', start_cash: float) -> tuple[bool, PlayerModel]:
    """
    :return: (flag, PlayerModel). Flag is True if new players was created
    """

    flag = False
    db_user_data = await access.players.get_player_by_vk_id(ctx.chat_id, ctx.msg.from_id)
    if db_user_data is None:
        flag = True
        vk_user_data = (await access.vk.get_users([ctx.msg.from_id]))[0]
        await access.players.add_player(
            vk_id=vk_user_data.vk_id,
            chat_id=ctx.chat_id,
            first_name=vk_user_data.first_name,
            last_name=vk_user_data.last_name,
            birthday=vk_user_data.birthday,
            city=vk_user_data.city,
            start_cash=start_cash,
        )

    return flag, await access.players.get_player_by_vk_id(ctx.chat_id, ctx.msg.from_id)


async def complete_registration(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = f'''
    Все игроки зарегистрированы. %0A
    Укажите сумму ставки без пробелов.%0A%0A
    Правила ставок:%0A{ctx.game.min_max_bet_info}%0A
    Ваши счета: %0A{ctx.game.players_cashes_info}
    '''
    await send(ctx, access, answer, Kbds.GET_OUT)

    ctx.state = States.WAITING_FOR_BETS


async def complete_betting(ctx: GameCtxProxy, access: 'GAccessors'):
    answer = 'Все игроки поставили ставки! Начинаю раздачу карт...'
    await send(ctx, access, answer, Kbds.EMPTY)


async def hand_out_cards(ctx: GameCtxProxy, access: 'GAccessors'):
    g = ctx.game
    # TODO get_card

    try:
        g.deal_cards()
    except IndexError as e:
        await do_end(ctx, access)
        await send(ctx, access, 'Колода закончилась! Данная игра не может быть продолжена', Kbds.START)
        ctx.state = States.WAITING_FOR_START_CHOICE
    else:
        txt = f'%0A%0A'.join([f'◾ {p}%0A{p.cards_info}' for p in g.players_and_dealer])
        await send(ctx, access, txt)

    # for player in ctx.game.players_and_dealer:
    #     await send(ctx, access, f'{player}%0A{player.cards}')
    # await send(ctx, access, f'{player}', photos=player.cards_photos)


async def bj_ask_player(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    player, dealer = ctx.game.current_player, ctx.game.dealer

    ctx.game.handle_player_blackjack(player)

    answer = f'{player}, У тебя блэкджек!%0A'

    if player.status_is_bj_need_to_clarify:
        answer += 'Выбирай'
        kbd = Kbds.BJ_DEALER_WITH_ACE
    elif player.status_is_bj_win32:
        answer += f'Поздравляем с победой!'
        kbd = Kbds.BJ_WIN_32
    else:
        answer += 'Жди конца игры'
        kbd = Kbds.BJ_DEALER_WITHOUT_ACE

    await send(ctx, access, answer, kbd=kbd)


async def ask_player(ctx: GameCtxProxy, access: 'GAccessors'):
    curr_player = ctx.game.current_player

    if curr_player.has_blackjack:
        await bj_ask_player(ctx, access)
    else:
        await base_ask_player(ctx, access)


async def base_ask_player(ctx: GameCtxProxy, access: 'GAccessors'):
    player, dealer = ctx.game.current_player, ctx.game.dealer
    answer = f'{player}, Сумма очков: {player.score} ({dealer}: {dealer.score})'
    await send(ctx, access, answer, kbd=Kbds.CHOOSE_ACTION)


async def handle_bj_pick_up11_action(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> bool:
    player.set_bj_win11_status()
    answer = f'{player}%0A, забирай 1:1!'
    await send(ctx, access, answer)
    return True


async def handle_bj_pick_up32_action(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> bool:
    return True


async def handle_bj_wait_action(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> bool:
    player.set_bj_waiting_for_end_status()
    answer = f'{player}, ожидай конца игры!'
    await send(ctx, access, answer)
    return True


async def handle_hit_action(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> bool:
    # TODO get_card
    try:
        player.add_card(ctx.game.deck.get_card())
    except IndexError as e:
        await do_end(ctx, access)
        await send(ctx, access, 'Колода закончилась! Данная игра не может быть продолжена', Kbds.START)
        ctx.state = States.WAITING_FOR_START_CHOICE
    else:
        answer = f'{player}%0A{player.cards_info}'
        await send(ctx, access, answer)
        return player.not_bust


async def handle_player_bust(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> bool:
    player.set_bust_status()
    answer = f'{player}, много! (Сумма: {player.score})'
    await send(ctx, access, answer)
    return True


async def handle_stand_action(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> bool:
    return True


async def dispatch(ctx: GameCtxProxy, access: 'GAccessors', player: Player, choice: Choices, action_res: bool) -> None:
    if choice is Choices.HIT and action_res and player.score != 21:
        await base_ask_player(ctx, access)
        return

    if choice is Choices.HIT and not action_res:
        await handle_player_bust(ctx, access, player)

    if ctx.game.next_player():
        await ask_player(ctx, access)
    else:
        # TODO get_card
        try:
            ctx.game.handle_dealer()
        except IndexError as e:
            await do_end(ctx, access)
            await send(ctx, access, 'Колода закончилась! Данная игра не может быть продолжена', Kbds.START)
            ctx.state = States.WAITING_FOR_START_CHOICE
        else:
            await handle_results(ctx, access)
            await show_results(ctx, access)
            ctx.state = States.WAITING_FOR_LAST_CHOICE


async def handle_results(ctx: GameCtxProxy, access: 'GAccessors'):
    ctx.game.define_results()
    await update_cashes(ctx, access)


async def show_results(ctx: GameCtxProxy, access: 'GAccessors'):
    game = ctx.game
    d = game.dealer
    answer = f'◾ {d}%0A{d.cards_info}%0A%0AСумма очков: {d.score}'
    if d.has_blackjack:
        answer += '(Блэк-джек)'
    await send(ctx, access, answer)

    answer = f'''
    Результаты игры:%0A
    {'%0A'.join([f'🔺 {p} - {p.status.value} (Счет: {p.cash})' for p in game.players])} 
    '''
    await send(ctx, access, answer, Kbds.REPEAT_GAME_QUESTION)


async def init_game(ctx: GameCtxProxy, access: 'GAccessors', num_of_players: int) -> None:
    sets = await access.settings.get(_id=0)
    ctx.game = BlackJackGame(
        chat_id=ctx.msg.peer_id,
        players_qty=num_of_players,
        min_bet=sets.min_bet,
        max_bet=sets.max_bet,
        decks_qty=sets.num_of_decks,
    )


async def player_in_game(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    sets = await access.settings.get(_id=0)
    _, db_player_data = await fetch_user_info(ctx, access, sets.start_cash)
    new_player = Player(name=db_player_data.first_name, vk_id=db_player_data.vk_id, cash=db_player_data.cash)

    if ctx.game.add_player(new_player):
        answer = f'{new_player}, ты в игре! (Зарегистрировано: {ctx.game.ratio_of_registered})'
    else:
        answer = f'{new_player}, ты уже в игре. Дождись остальных игроков!'

    await send(ctx, access, answer, Kbds.CONFIRM)


async def place_bet(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> None:
    if (bet := parse_bet_expr(ctx.msg.text)) is None or bet < 0:
        answer = f'{player}, вы указали некорректную сумму ставки'
    elif bet > player.cash:
        answer = f'{player}, на счете недостаточно денег, дружище. На счете: {player.cash}'
    elif bet > ctx.game.max_bet:
        answer = f'{player}, ты превысил максимальную ставку стола%0A{ctx.game.min_max_bet_info}'
    elif bet < ctx.game.min_bet:
        answer = f'{player}, твоя ставка ниже минимальной ставки стола%0A{ctx.game.min_max_bet_info}'
    else:
        answer = f'{player}, ваша ставка принята! Сумма ставки: {bet}'
        player.place_bet(bet)

    await send(ctx, access, answer, Kbds.GET_OUT)


async def repeat_game(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = f'''Круто, играем снова! Укажите сумму ставки без пробелов.%0A%0A
                Ваши счета: %0A{ctx.game.players_cashes_info}
                '''
    await send(ctx, access, answer, Kbds.GET_OUT)

    ctx.game.reset()
    ctx.state = States.WAITING_FOR_BETS


async def end_game(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = f'Окей, больше не играем!'
    await send(ctx, access, answer)
    await do_end(ctx, access)


async def update_cashes(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    for player in ctx.game.players:
        await access.players.update_cash(ctx.chat_id, player.vk_id, player.cash)


async def do_cancel(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    await hide_keyboard(ctx, access, 'Отмена игры')
    await do_end(ctx, access)


async def do_end(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    del ctx.state
    del ctx.game


async def do_back(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    ctx.state = ctx.last_state


def check_back(payload: str) -> bool:
    return payload == 'back'


def check_cancel(payload: str) -> bool:
    return payload == 'cancel'


async def hide_keyboard(ctx: GameCtxProxy, access: 'GAccessors', text: str) -> None:
    await send(ctx, access, text)


def pretty_datetime(raw: datetime) -> str:
    return raw.strftime('%b %d %Y в %I:%M%p')


async def send(ctx: GameCtxProxy, access: 'GAccessors', txt: str, kbd: Keyboard = Kbds.EMPTY, photos: str = ''):
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=txt, kbd=kbd, photos=photos))
