import typing
from typing import Optional

from proj.store.vk.dataclasses import UpdateMessage

from .game import BlackJackGame
from .middlewares import StateResolverMiddleware
from .states import State, States

if typing.TYPE_CHECKING:
    from .accessors import GameCtxAccessor

__all__ = (
    "FSMGameCtx",
    "FSMGameCtxProxy",
)


class FSMGameCtx:
    def __init__(
        self, accessor: "GameCtxAccessor", chat: int, msg: UpdateMessage
    ) -> None:
        self.chat = chat
        self.msg = msg
        self._accessor = accessor

    def proxy(self) -> "FSMGameCtxProxy":
        return FSMGameCtxProxy(self)

    async def get_state(self, default: Optional[int] = None) -> Optional[State]:
        state_id = await self._accessor.get_state(chat=self.chat, default=default)
        return (
            default
            if state_id is None
            else StateResolverMiddleware.state_by_id(state_id)
        )

    async def get_game(self, default: Optional[dict] = None) -> Optional[BlackJackGame]:
        raw_game = await self._accessor.get_data(chat=self.chat, default=default)
        return default if raw_game is None else BlackJackGame(raw=raw_game)

    async def set_state(self, state: State) -> None:
        if state is None:
            await self.reset_state()
        else:
            await self._accessor.set_state(chat=self.chat, state=state.state_id)

    async def save_game(self, game: Optional[BlackJackGame]) -> None:
        if game is None:
            await self.reset_game()
        else:
            await self._accessor.set_data(chat=self.chat, data=game.to_dict())

    async def reset_game(self) -> None:
        await self._accessor.reset_data(chat=self.chat)

    async def reset_state(self) -> None:
        await self._accessor.reset_state(chat=self.chat)


class FSMGameCtxProxy:
    def __init__(self, context: FSMGameCtx) -> None:
        self._context = context
        self._game: Optional[BlackJackGame] = None
        self._state: Optional[State] = None
        self._last_state: Optional[State] = None

        self._state_is_dirty = False

        self._closed = True

    @property
    def ctx(self) -> FSMGameCtx:
        return self._context

    async def __aenter__(self):
        await self.load()

        if not self._state:
            self.state = States.WAITING_FOR_TRIGGER

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.save()
            self._closed = True
            return

        raise Exception("SHIT")
        # TODO: raise exception

    @property
    def chat_id(self) -> int:
        return self.ctx.chat

    async def load(self) -> None:
        self._closed = False

        self._state = await self.ctx.get_state()
        self._game = await self.ctx.get_game()
        self._state_is_dirty = False

    async def save(self, force: bool = False) -> None:
        # TODO check usage of game
        # if self.game is not None:
        await self.ctx.save_game(game=self._game)

        if self._state_is_dirty or force:
            await self.ctx.set_state(state=self._state)

        self._state_is_dirty = False

    def rollback_state(self) -> None:
        self._state = self._last_state
        self._last_state = None

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, value: State) -> None:
        self._last_state = self.state
        self._state_is_dirty = True
        self._state = value

    @property
    def msg(self) -> UpdateMessage:
        return self.ctx.msg

    @property
    def last_state(self) -> State:
        return self._last_state

    @state.deleter
    def state(self) -> None:
        self._state_is_dirty = True
        self._state = None

    @property
    def game(self) -> BlackJackGame:
        return self._game

    @game.setter
    def game(self, value: BlackJackGame) -> None:
        self._game = value

    @game.deleter
    def game(self) -> None:
        self._game = None
