from app.game.deck import Card
from app.game.logic import *
from app.game.states import States
from app.game.utils import get_payload, Choice

if TYPE_CHECKING:
    from app.game.dataclasses import GAccessors

START_MSG = '/go'


@States.WAITING_FOR_TRIGGER.register
async def trigger_received(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if START_MSG in ctx.msg.text:
        answer = 'Дарова!'
        await send(ctx, access, answer, kbd=Kbds.START, photos=Card.joker_photo)
        ctx.state = States.WAITING_FOR_START_CHOICE


@States.WAITING_FOR_START_CHOICE.register
async def start_menu_clicked(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    choose = {
        'new_game': lambda: handle_new_game(ctx, access),
        'bonus': lambda: handle_bonus(ctx, access),
        'balance': lambda: handle_balance(ctx, access),
        'cancel': lambda: do_cancel(ctx, access),
    }

    await choose[payload]()


@States.WAITING_FOR_PLAYERS_COUNT.register
async def players_amount_clicked(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    if payload == 'cancel':
        await do_cancel(ctx, access)
        return

    if payload not in '123':
        return

    await hide_keyboard(ctx, access, f'Количество игроков: {payload}')
    await init_game(ctx, access, int(payload))

    answer = 'Отлично! Чтобы зарегистрироваться на игру, желающие должны нажать кнопку:'
    await send(ctx, access, answer, Kbds.CONFIRM)

    ctx.state = States.WAITING_FOR_REGISTER


@States.WAITING_FOR_REGISTER.register
async def registration_clicked(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    if payload == 'cancel':
        await do_cancel(ctx, access)
        return

    if payload != 'register':
        return

    await register_player(ctx, access)

    if ctx.game.all_players_registered:
        await complete_registration(ctx, access)


@States.WAITING_FOR_BETS.register
async def bet_received(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (player := ctx.game.get_player_by_id(ctx.msg.from_id)) is None:
        return

    await place_bet(ctx, access, player)

    if ctx.game.all_players_bet:
        await complete_betting(ctx, access)


@States.WAITING_FOR_ACTION.register
async def action_clicked(ctx: GameCtxProxy, access: 'GAccessors'):
    player = ctx.game.current_player
    choose = {
        'hit': lambda: handle_hit_action(ctx, access, player),
        'stand': lambda: handle_next_player(ctx, access),
    }

    if ctx.msg.from_id != player.vk_id:
        return

    try:
        choice = Choice(get_payload(ctx.msg))
    except ValueError:
        return
    else:
        await choose[choice]()


@States.WAITING_FOR_ANSWER_TO_REPEAT_QUESTION.register
async def last_action_clicked(ctx: GameCtxProxy, access: 'GAccessors'):
    if (payload := get_payload(ctx.msg)) is None:
        return

    choose = {
        'stop': lambda: end_game(ctx, access),
        'again': lambda: repeat_game(ctx, access),
    }

    try:
        await choose[payload]()
    except KeyError:
        print('Bad payload')

