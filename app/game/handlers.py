from typing import TYPE_CHECKING

from app.game.deck import Card
from app.game.game import GameCtxProxy, BlackJackGame
from app.api.player.models import PlayerModel
from app.game.player import Player
from app.game.states import BJStates
from app.game.utils import parse_bet_expr, get_payload
from app.store.vk_api.dataclasses import Message

if TYPE_CHECKING:
    from app.game.dataclasses import GAccessors

START_MSG = '/go'


@BJStates.WAITING_FOR_TRIGGER.register
async def trigger_received(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if START_MSG in ctx.msg.text:
        answer = 'Сыграем?'
        await access.vk.send_message(
            Message(peer_id=ctx.msg.peer_id, text=answer, kbd=ctx.state.keyboard, photos=Card.joker_photo))
        ctx.state = BJStates.WAITING_FOR_NEW_GAME


@BJStates.WAITING_FOR_NEW_GAME.register
async def new_game_clicked(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    if check_cancel(payload):
        await do_cancel(ctx, access)
        return

    if payload == 'new_game':
        answer = 'Выберите количество игроков'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, kbd=ctx.state.keyboard))
        ctx.state = BJStates.WAITING_FOR_PLAYERS_COUNT


async def do_cancel(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    await hide_keyboard(ctx, access, 'Отмена игры')
    await do_end(ctx, access)


async def do_end(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    del ctx.state
    del ctx.game


def check_back(payload: str) -> bool:
    return payload == 'back'


def check_cancel(payload: str) -> bool:
    return payload == 'cancel'


@BJStates.WAITING_FOR_PLAYERS_COUNT.register
async def player_numbers_clicked(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    if check_cancel(payload):
        await do_cancel(ctx, access)
        return

    choice = int(payload)
    if choice in (1, 2, 3):
        await hide_keyboard(ctx, access, f'Количество игроков: {choice}')

        answer = 'Отлично! Чтобы зарегистрироваться на игру, желающие должны нажать кнопку:'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, kbd=ctx.state.keyboard))

        ctx.game = BlackJackGame(chat_id=ctx.msg.peer_id, num_of_players=choice)
        ctx.state = BJStates.WAITING_FOR_REGISTER


async def hide_keyboard(ctx: GameCtxProxy, access: 'GAccessors', text: str) -> None:
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=text))


async def handle_userinfo(access: 'GAccessors', uid: int) -> PlayerModel:
    db_user_data = await access.players.get_by_vk_id(uid)
    if db_user_data is None:
        vk_user_data = (await access.vk.get_users([uid]))[0]
        await access.players.add(
            vk_id=vk_user_data.vk_id,
            first_name=vk_user_data.first_name,
            last_name=vk_user_data.last_name,
            birthday=vk_user_data.birthday,
            city=vk_user_data.city,
        )
    return await access.players.get_by_vk_id(uid)


@BJStates.WAITING_FOR_REGISTER.register
async def player_registered(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    if check_cancel(payload):
        await do_cancel(ctx, access)
        return

    if payload == 'register':
        db_player_data = await handle_userinfo(access, ctx.msg.from_id)
        new_player = Player(name=db_player_data.first_name, vk_id=db_player_data.vk_id)

        if ctx.game.add_player(new_player):
            answer = f'{new_player}, ты в игре! (Зарегистрировано: {ctx.game.ratio_of_registered})'
        else:
            answer = f'{new_player}, ты уже в игре. Дождись остальных игроков!'

        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, kbd=ctx.state.keyboard))

        if ctx.game.all_players_registered:
            await complete_registration(ctx, access)


async def complete_registration(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    answer = 'Все игроки зарегистрированы. Игра начинается! %0A Укажите сумму ставки без пробелов.'
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))
    ctx.state = BJStates.WAITING_FOR_BETS


@BJStates.WAITING_FOR_BETS.register
async def bet_placed(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (player := ctx.game.get_player_by_id(ctx.msg.from_id)) is not None:
        if (bet := parse_bet_expr(ctx.msg.text)) is None:
            answer = f'{player}, вы указали некорректную сумму ставки'
        else:
            answer = f'{player}, ваша ставка принята! Сумма ставки: {bet}'
            player.place_bet(bet)

        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))

        if ctx.game.all_players_bet:
            await complete_betting(ctx, access)


async def complete_betting(ctx: GameCtxProxy, access: 'GAccessors'):
    answer = 'Все игроки поставили ставки! Начинаю раздачу карт...'
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))
    await hand_out_cards(ctx, access)


async def hand_out_cards(ctx: GameCtxProxy, access: 'GAccessors'):
    ctx.game.deal_cards()

    for player in ctx.game.players_and_dealer:
        answer = f'{player}, Сумма очков: {player.score}'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, photos=player.cards_photos))

    await ask_player(ctx, access)


async def ask_player(ctx: GameCtxProxy, access: 'GAccessors'):
    player = ctx.game.current_player
    answer = f'{player}, Сумма очков: {player.score} Ваш выбор?'
    ctx.state = BJStates.WAITING_FOR_ACTION  # because need to use state.keyboard
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, kbd=ctx.state.keyboard))


@BJStates.WAITING_FOR_ACTION.register
async def handling_action(ctx: GameCtxProxy, access: 'GAccessors'):
    player = ctx.game.current_player
    choose = {
        'hit': lambda: handle_hit_action(ctx, access, player),
        'stand': lambda: handle_next_player(ctx, access),
    }

    # TODO add choose-object for player
    if (choice := get_payload(ctx.msg)) in ('hit', 'stand') and ctx.msg.from_id == player.vk_id:
        await choose[choice]()


async def handle_hit_action(ctx: GameCtxProxy, access: 'GAccessors', player: Player) -> None:
    card = ctx.game.deck.get_card()
    player.add_card(card)

    answer = f'{player}, твои карты:'
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, photos=player.cards_photos))

    if player.in_game:
        await ask_player(ctx, access)
    else:
        answer = f'{player}, перебор! (Сумма: {player.score})'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))
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
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, photos=dealer.cards_photos))

    for player in ctx.game.players:
        answer = f'{player}, {ctx.game.define_result(player).value}'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))

    await play_again_request(ctx, access)


async def play_again_request(ctx: GameCtxProxy, access: 'GAccessors'):
    answer = f'Выбирай'
    ctx.state = BJStates.WAITING_FOR_ANSWER_TO_REPEAT_QUESTION
    await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer, kbd=ctx.state.keyboard))


@BJStates.WAITING_FOR_ANSWER_TO_REPEAT_QUESTION.register
async def handle_play_again_response(ctx: GameCtxProxy, access: 'GAccessors'):
    if (payload := get_payload(ctx.msg)) is None:
        return

    if payload == 'stop':
        answer = f'Окей, больше не играем!'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))
        await do_end(ctx, access)
    else:
        answer = f'Круто, играем снова! Укажите сумму ставки без пробелов.'
        await access.vk.send_message(Message(peer_id=ctx.msg.peer_id, text=answer))
        ctx.game.reset()
        ctx.state = BJStates.WAITING_FOR_BETS
