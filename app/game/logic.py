from datetime import datetime, timedelta as td
from typing import TYPE_CHECKING

from app.api.player.models import PlayerModel
from app.game.game import GameCtxProxy, BlackJackGame
from app.game.keyboards import Keyboards as Kbds, Keyboard
from app.game.player import Player
from app.game.states import States
from app.game.utils import parse_bet_expr
from app.store.vk_api.dataclasses import Message

if TYPE_CHECKING:
    from app.game.dataclasses import GAccessors


def pretty_datetime(raw: datetime) -> str:
    return raw.strftime('%b %d %Y at %I:%M%p')


async def send(ctx: GameCtxProxy, access: 'GAccessors', txt: str, kbd: Keyboard = Kbds.EMPTY, photos: str = ''):
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=txt, kbd=kbd, photos=photos))


async def handle_new_game(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = 'Выберите количество игроков'
    await send(ctx, access, answer, kbd=Kbds.NUMBER_OF_PLAYERS)
    ctx.state = States.WAITING_FOR_PLAYERS_COUNT


async def handle_balance(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    sets = await access.settings.get(_id=0)
    created, player = await handle_userinfo(access, ctx.msg.from_id, sets.start_cash)

    answer = f'Баланс твоего счета: {player.cash} у.е.'
    await send(ctx, access, answer, Kbds.START)
    ctx.state = States.WAITING_FOR_START_CHOICE


async def handle_bonus(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    sets = await access.settings.get(_id=0)
    created, player = await handle_userinfo(access, ctx.msg.from_id, sets.start_cash)

    if created:
        answer = f'''А вы у нас впервые, получайте свой бонус: {sets.bonus} у.е.%0A
        Следующий бонус будет доступен {pretty_datetime(td(minutes=sets.bonus_period) + datetime.now())}'''
    elif player.check_bonus(sets.bonus_period):
        answer = f'''Вы получаете ежедневный бонус: {sets.bonus} у.е.%0A
        Следующий бонус будет доступен {pretty_datetime(td(minutes=sets.bonus_period) + datetime.now())}'''
        await access.players.give_bonus(player.vk_id, player.cash + sets.bonus)
    else:
        answer = f'''К сожалению бонус еще не доступен :(%0A
        Ближайший бонус будет доступен {pretty_datetime(td(minutes=sets.bonus_period) + player.last_bonus_date)}'''

    await send(ctx, access, answer, Kbds.START)


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


async def handle_userinfo(access: 'GAccessors', uid: int, start_cash: float) -> tuple[bool, PlayerModel]:
    """

    :param access:
    :param uid:
    :param start_cash:
    :return: (flag, PlayerModel). Flag is True if new player was created
    """

    flag = False
    db_user_data = await access.players.get_by_vk_id(uid)
    if db_user_data is None:
        flag = True
        vk_user_data = (await access.vk.get_users([uid]))[0]
        await access.players.add(
            vk_id=vk_user_data.vk_id,
            first_name=vk_user_data.first_name,
            last_name=vk_user_data.last_name,
            birthday=vk_user_data.birthday,
            city=vk_user_data.city,
            start_cash=start_cash
        )

    return flag, await access.players.get_by_vk_id(uid)


async def complete_registration(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = f'''
    Все игроки зарегистрированы. %0A
    Укажите сумму ставки без пробелов.%0A%0A
    Правила ставок:%0A{ctx.game.min_max_bet_info}%0A
    Ваши счета: %0A{'%0A'.join([f'{p} - {p.cash}' for p in ctx.game.players])}
    '''
    await send(ctx, access, answer)

    ctx.state = States.WAITING_FOR_BETS


async def complete_betting(ctx: GameCtxProxy, access: 'GAccessors'):
    answer = 'Все игроки поставили ставки! Начинаю раздачу карт...'
    await send(ctx, access, answer)

    await hand_out_cards(ctx, access)


async def hand_out_cards(ctx: GameCtxProxy, access: 'GAccessors'):
    ctx.game.deal_cards()

    for player in ctx.game.players_and_dealer:
        answer = f'{player}, Сумма очков: {player.score}'
        await send(ctx, access, answer, photos=player.cards_photos)

    await ask_player(ctx, access)


async def ask_player(ctx: GameCtxProxy, access: 'GAccessors'):
    player = ctx.game.current_player
    answer = f'{player}, Сумма очков: {player.score} Ваш выбор?'
    ctx.state = States.WAITING_FOR_ACTION  # because need to use state.keyboard
    await send(ctx, access, answer, kbd=Kbds.CHOOSE_ACTION)


async def handle_hit_action(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> None:
    card = ctx.game.deck.get_card()
    player.add_card(card)

    answer = f'{player}, твои карты:'
    await send(ctx, access, answer, photos=player.cards_photos)

    if player.in_game:
        await ask_player(ctx, access)
    else:
        answer = f'{player}, перебор! (Сумма: {player.score})'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))
        await send(ctx, access, answer)

        await handle_next_player(ctx, access)


async def handle_next_player(ctx: GameCtxProxy, access: 'GAccessors'):
    if ctx.game.next_player():
        await ask_player(ctx, access)
    else:
        ctx.game.handle_dealer()
        await show_results(ctx, access)


async def show_results(ctx: GameCtxProxy, access: 'GAccessors'):
    dealer = ctx.game.dealer
    answer = f'Дилер, Сумма очков: {dealer.score}'
    await send(ctx, access, answer, photos=dealer.cards_photos)

    for player in ctx.game.players:
        answer = f'{player}, {ctx.game.define_result(player).value}'
        await send(ctx, access, answer)

    await update_cashes(ctx, access)


async def play_again_request(ctx: GameCtxProxy, access: 'GAccessors'):
    answer = f'Выбирай'
    ctx.state = States.WAITING_FOR_ANSWER_TO_REPEAT_QUESTION
    await send(ctx, access, answer, Kbds.REPEAT_GAME_QUESTION)


async def init_game(ctx: GameCtxProxy, access: 'GAccessors', num_of_players: int) -> None:
    sets = await access.settings.get(_id=0)
    ctx.game = BlackJackGame(
        chat_id=ctx.msg.peer_id,
        num_of_players=num_of_players,
        min_bet=sets.min_bet,
        max_bet=sets.max_bet,
        num_of_decks=sets.num_of_decks,
    )


async def register_player(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    sets = await access.settings.get(_id=0)
    _, db_player_data = await handle_userinfo(access, ctx.msg.from_id, sets.start_cash)
    new_player = Player(name=db_player_data.first_name, vk_id=db_player_data.vk_id, cash=db_player_data.cash)

    if ctx.game.add_player(new_player):
        answer = f'{new_player}, ты в игре! (Зарегистрировано: {ctx.game.ratio_of_registered})'
    else:
        answer = f'{new_player}, ты уже в игре. Дождись остальных игроков!'

    await send(ctx, access, answer)


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

    await send(ctx, access, answer)


async def repeat_game(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = f'''
                Круто, играем снова! Укажите сумму ставки без пробелов.%0A%0A
                Ваши счета: %0A{'%0A'.join([f'{p} - {p.cash}' for p in ctx.game.players])}
                '''
    await send(ctx, access, answer)

    ctx.game.reset()
    ctx.state = States.WAITING_FOR_BETS


async def end_game(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = f'Окей, больше не играем!'
    await send(ctx, access, answer)
    await do_end(ctx, access)


async def update_cashes(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    for player in ctx.game.players:
        ctx.game.update_cash(player)
        await access.players.update_cash(player.vk_id, player.cash)

    answer = f'''
            Ваши счета: %0A{'%0A'.join([f'{p} - {p.cash}' for p in ctx.game.players])}
            '''
    await send(ctx, access, answer)
    await play_again_request(ctx, access)
