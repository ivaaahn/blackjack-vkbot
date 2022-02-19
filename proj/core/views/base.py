import logging
import typing
from typing import Generic, TypeVar, Generator, Any, Optional

from proj.store import CoreStore
from proj.store.base import S
from proj.store.vk.keyboards import Keyboard, Keyboards
from ..game import BlackJackGame

if typing.TYPE_CHECKING:
    from ..accessors import GameInteractionAccessor
    from ..context import FSMGameCtxProxy
    from ..states import State


ContextProxy = TypeVar("ContextProxy")


class AbstractBotView(Generic[S, ContextProxy]):
    class Meta:
        name = "abstract"

    def __init__(self, store: S, context: ContextProxy) -> None:
        self._store = store
        self._context = context

    @property
    def store(self) -> S:
        return self._store

    @property
    def ctx(self) -> ContextProxy:
        return self._context

    def __await__(self) -> Generator[Any, None, None]:
        pass


class BotView(AbstractBotView[CoreStore, "FSMGameCtxProxy"]):
    def __init__(self, store: CoreStore, context: "FSMGameCtxProxy") -> None:
        super().__init__(store, context)
        self._name = self.Meta.name or self.__class__.__name__
        self._logger = store.app.get_logger(f"View {self._name}")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def execute(self) -> Optional["State"]:
        pass

    async def pre_handle(self):
        pass

    async def post_handle(self, next_state: Optional["State"]):
        pass

    async def _iter(self):
        try:
            await self.pre_handle()
            resp = await self.execute()
            await self.post_handle(resp)
        except Exception as err:
            if res := self.handle_exception(err) is None:
                raise err

            return res

    def __await__(self) -> Generator[Any, None, None]:
        return self._iter().__await__()

    def handle_exception(self, e: Exception):
        pass

    async def send(
        self,
        txt: str,
        kbd: Keyboard = Keyboards.EMPTY,
        photos: str = "",
    ):
        await self.store.game_interact.send(self.ctx, txt, kbd, photos)

    @property
    def interact(self) -> "GameInteractionAccessor":
        return self.store.game_interact

    @property
    def game(self) -> BlackJackGame:
        return self.ctx.game
