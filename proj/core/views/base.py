import json
import logging
import typing
from typing import Generic, TypeVar, Generator, Any, Optional

from proj.store import CoreStore
from proj.store.base import S
from proj.store.vk.keyboards import Keyboard, Keyboards
from ..game import BlackJackGame

if typing.TYPE_CHECKING:
    from proj.store.vk.dataclasses import UpdateMessage
    from ..accessors import GameInteractionAccessor
    from ..context import FSMGameCtxProxy
    from ..states import State


ContextProxy = TypeVar("ContextProxy")


class AbstractBotView(Generic[S, ContextProxy]):
    class Meta:
        name = None

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
        self._payload_btn: Optional[str] = None

    @property
    def payload_btn(self) -> str:
        return self._payload_btn

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def execute(self) -> Optional["State"]:
        pass

    @staticmethod
    def _get_payload(msg: "UpdateMessage", key: str) -> Optional[str]:
        if msg.payload is None:
            return None

        payload_json = json.loads(msg.payload)
        return payload_json.get(key)

    def _get_btn_payload(self) -> None:
        self._payload_btn = self._get_payload(self.ctx.msg, "button")

    async def _handle_cancel(self) -> bool:
        if self.payload_btn == "cancel":
            await self.interact._do_cancel(self.ctx)
            return True

        return False

    async def pre_handle(self):
        self._get_btn_payload()

    async def post_handle(self, next_state: Optional["State"]):
        pass

    async def _iter(self):
        try:
            await self.pre_handle()

            if not await self._handle_cancel():
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
        await self.store.game_interact._send(self.ctx, txt, kbd, photos)

    @property
    def interact(self) -> "GameInteractionAccessor":
        return self.store.game_interact

    @property
    def game(self) -> BlackJackGame:
        return self.ctx.game
