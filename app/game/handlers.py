import json

from app.game.game import GameCtxProxy, BlackJackGame
from app.game.player import Player
from app.game.states import BJStates
from app.game.utils import parse_bet_expr, get_username_by_id, get_payload
from app.store.vk_api.dataclasses import Message, UpdateMessage

START_MSG = '/go'


@BJStates.WAITING_FOR_TRIGGER.register
async def trigger_received(vk_api, ctx: GameCtxProxy, msg: UpdateMessage) -> None:
    if START_MSG in msg.text:
        answer = 'Сыграем?'
        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, kbd=ctx.state.keyboard))
        ctx.state = BJStates.WAITING_FOR_NEW_GAME


@BJStates.WAITING_FOR_NEW_GAME.register
async def new_game_clicked(vk_api, ctx: GameCtxProxy, msg: UpdateMessage) -> None:
    if (payload := get_payload(msg)) is None:
        return

    if check_cancel(payload):
        await do_cancel(vk_api, ctx, msg)
        return

    if payload == 'new_game':
        answer = 'Выберите количество игроков'
        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, kbd=ctx.state.keyboard))
        ctx.state = BJStates.WAITING_FOR_PLAYERS_COUNT


async def do_cancel(vk_api, ctx: GameCtxProxy, msg: UpdateMessage) -> None:
    await hide_keyboard(vk_api, ctx, msg, 'Отмена игры')
    del ctx.state


def check_back(payload: str) -> bool:
    return payload == 'back'


def check_cancel(payload: str) -> bool:
    return payload == 'cancel'


@BJStates.WAITING_FOR_PLAYERS_COUNT.register
async def player_numbers_clicked(vk_api, ctx: GameCtxProxy, msg: UpdateMessage) -> None:
    if (payload := get_payload(msg)) is None:
        return

    if check_cancel(payload):
        await do_cancel(vk_api, ctx, msg)
        return

    choice = int(payload)
    if choice in (1, 2, 3):
        await hide_keyboard(vk_api, ctx, msg, f'Количество игроков: {choice}')

        answer = 'Отлично! Чтобы зарегистрироваться на игру, желающие должны нажать кнопку:'
        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, kbd=ctx.state.keyboard))

        ctx.game = BlackJackGame(chat_id=msg.peer_id, num_of_players=choice)
        ctx.state = BJStates.WAITING_FOR_REGISTER


# And hide keyboard
async def hide_keyboard(vk_api, _: GameCtxProxy, msg: UpdateMessage, text: str) -> None:
    await vk_api.send_message(Message(peer_id=msg.peer_id, text=text))


@BJStates.WAITING_FOR_REGISTER.register
async def player_registered(vk_api, ctx: GameCtxProxy, msg: UpdateMessage) -> None:
    if (payload := get_payload(msg)) is None:
        return

    if check_cancel(payload):
        await do_cancel(vk_api, ctx, msg)
        return

    if payload == 'register':
        chat = await vk_api.get_chat(msg.peer_id)  # TODO chat to dataclass
        sender_name = get_username_by_id(msg.from_id, chat)

        new_player = Player(sender_name, msg.from_id)
        if ctx.game.add_player(new_player):
            answer = f'{new_player}, ты в игре! (Зарегистрировано: {ctx.game.ratio_of_registered})'
        else:
            answer = f'{new_player}, ты уже в игре. Дождись остальных игроков!'

        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, kbd=ctx.state.keyboard))

        if ctx.game.all_players_registered:
            await complete_registration(vk_api, ctx, msg)


async def complete_registration(vk_api, ctx: GameCtxProxy, msg: UpdateMessage):
    answer = 'Все игроки зарегистрированы. Игра начинается! %0A Укажите сумму ставки без пробелов.'
    await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer))
    ctx.state = BJStates.WAITING_FOR_BETS


@BJStates.WAITING_FOR_BETS.register
async def bet_placed(vk_api, ctx: GameCtxProxy, msg: UpdateMessage) -> None:
    if (player := ctx.game.get_player_by_id(msg.from_id)) is not None:
        if (bet := parse_bet_expr(msg.text)) is None:
            answer = f'{player}, вы указали некорректную сумму ставки'
        else:
            answer = f'{player}, ваша ставка принята! Сумма ставки: {bet}'
            player.place_bet(bet)

        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer))

        if ctx.game.all_players_bet:
            await complete_betting(vk_api, ctx, msg)


async def complete_betting(vk_api, ctx: GameCtxProxy, msg: UpdateMessage):
    answer = 'Все игроки поставили ставки! Начинаю раздачу карт...'
    await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer))
    await hand_out_cards(vk_api, ctx, msg)


async def hand_out_cards(vk_api, ctx: GameCtxProxy, msg: UpdateMessage):
    ctx.game.deal_cards()

    for player in ctx.game.players_and_dealer:
        # answer = f'{player}, %0a{player.cards}%0aСумма: {player.score}'
        answer = f'{player}, Сумма очков: {player.score}'
        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, photos=player.cards_photos))

    await ask_player(vk_api, ctx, msg)


async def ask_player(vk_api, ctx: GameCtxProxy, msg: UpdateMessage):
    player = ctx.game.current_player
    answer = f'{player}, Сумма очков: {player.score} Ваш выбор?'
    ctx.state = BJStates.WAITING_FOR_ACTION  # Here, 'cause need to use state.keyboard
    await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, kbd=ctx.state.keyboard))


@BJStates.WAITING_FOR_ACTION.register
async def handling_action(vk_api, ctx: GameCtxProxy, msg: UpdateMessage):
    player = ctx.game.current_player
    # TODO Is it work normal?
    choose = {
        'hit': lambda: handle_hit_action(vk_api, ctx, msg, player),
        'stand': lambda: handle_next_player(vk_api, ctx, msg),
    }

    # TODO add choose-object for player
    if (choice := get_payload(msg)) in ('hit', 'stand') and msg.from_id == player.vk_id:
        await choose[choice]()


async def handle_hit_action(vk_api, ctx: GameCtxProxy, msg: UpdateMessage, player: Player) -> None:
    card = ctx.game.deck.get_card()
    player.add_card(card)

    # answer = f'{player},%0aНовая карта: {card}%0a%0aВсе карты: {player.cards}%0aСумма очков: {player.score}'

    answer = f'{player}, твои карты:'
    await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, photos=player.cards_photos))

    if player.in_game:
        await ask_player(vk_api, ctx, msg)
    else:
        answer = f'{player}, перебор! (Сумма: {player.score})'
        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer))
        await handle_next_player(vk_api, ctx, msg)


async def handle_next_player(vk_api, ctx: GameCtxProxy, msg: UpdateMessage):
    if ctx.game.next_player():
        await ask_player(vk_api, ctx, msg)
    else:
        ctx.game.handle_dealer()
        await show_results(vk_api, ctx, msg)


async def show_results(vk_api, ctx: GameCtxProxy, msg: UpdateMessage):
    # answer = f'Дилер, %0a{ctx.game.dealer.cards}%0aСумма очков: {ctx.game.dealer.score}'
    dealer = ctx.game.dealer
    answer = f'Дилер, Сумма очков: {dealer.score}'
    await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer, photos=dealer.cards_photos))

    for player in ctx.game.players:
        answer = f'{player}, {ctx.game.define_result(player).value}'
        await vk_api.send_message(Message(peer_id=msg.peer_id, text=answer))

    del ctx.state
