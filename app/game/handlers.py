from app.game.deck import Card
from app.game.logic import *
from app.game.states import States
from app.game.utils import get_payload, Choices

if TYPE_CHECKING:
    from app.game.dataclasses import GAccessors

START_MSG = '/go'


@States.WAITING_FOR_TRIGGER.register
async def trigger_received(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if START_MSG in ctx.msg.text:
        answer = 'Привет, меня зовут BlackjackBot!'
        await send(ctx, access, answer, kbd=Kbds.START)
        ctx.state = States.WAITING_FOR_START_CHOICE


@States.WAITING_FOR_START_CHOICE.register
async def start_action_clicked(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    choose = {
        'new_game': lambda: handle_new_game(ctx, access),
        'bonus': lambda: handle_bonus(ctx, access),
        'balance': lambda: handle_balance(ctx, access),
        'stat': lambda: handle_statistic(ctx, access),
        'cancel': lambda: do_cancel(ctx, access),
    }

    await choose[payload]()


@States.WAITING_FOR_PLAYERS_AMOUNT.register
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

    ctx.state = States.WAITING_FOR_REGISTRATION


@States.WAITING_FOR_REGISTRATION.register
async def registration_clicked(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (payload := get_payload(ctx.msg)) is None:
        return

    if payload == 'cancel':
        await do_cancel(ctx, access)
        return

    if payload != 'register':
        return

    await player_in_game(ctx, access)

    if ctx.game.all_players_registered:
        await complete_registration(ctx, access)


@States.WAITING_FOR_BETS.register
async def bet_received(ctx: GameCtxProxy, access: 'GAccessors') -> None:
    if (player := ctx.game.get_player_by_id(ctx.msg.from_id)) is None:
        return

    if get_payload(ctx.msg) == 'get out':
        await send(ctx, access, f'{player}, вы покидаете игру')
        ctx.game.drop_player(player)
        if not ctx.game.players:
            await do_cancel(ctx, access)
            return
    else:
        await place_bet(ctx, access, player)

    if ctx.game.all_players_bet:
        # await complete_betting(ctx, access)
        await hand_out_cards(ctx, access)
        await ask_player(ctx, access)
        ctx.state = States.WAITING_FOR_ACTION


@States.WAITING_FOR_ACTION.register
async def action_clicked(ctx: GameCtxProxy, access: 'GAccessors'):
    player = ctx.game.current_player

    if ctx.msg.from_id != player.vk_id:
        return

    actions = {
        Choices.HIT: lambda: handle_hit_action(ctx, access, player),
        Choices.STAND: lambda: handle_next_player(ctx, access),
    }

    try:
        choice = Choices(get_payload(ctx.msg))
    except ValueError:
        return
    else:
        await actions[choice]()


@States.WAITING_FOR_LAST_CHOICE.register
async def last_action_clicked(ctx: GameCtxProxy, access: 'GAccessors'):
    if (payload := get_payload(ctx.msg)) is None:
        return

    if ctx.msg.from_id not in ctx.game.players_ids:
        return

    actions = {
        'stop': lambda: end_game(ctx, access),
        'again': lambda: repeat_game(ctx, access),
    }

    try:
        await actions[payload]()
    except KeyError:
        print('Bad payload')

