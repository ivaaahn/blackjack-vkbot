import typing

from logging import getLogger
from typing import Type, Optional
from proj.store import Store
from ...services.app_logger import get_logger

if typing.TYPE_CHECKING:
    from ..context import FSMGameCtxProxy
    from ..states import State
    from ..views import BotView

__all__ = ("StateResolverMiddleware",)


logger = get_logger(__name__)


class StateResolverMiddleware:
    _STATE_VIEW: dict["State", Type["BotView"]] = {}

    _STATE_INSTANCE: dict[int, "State"] = {}

    @classmethod
    def add_state(cls, state: "State", view: Type["BotView"]) -> None:
        cls._STATE_VIEW[state] = view
        cls._STATE_INSTANCE[state.state_id] = state

    @classmethod
    def _resolve(cls, state: "State") -> Optional[Type["BotView"]]:
        return cls._STATE_VIEW.get(state)

    @classmethod
    async def exec(cls, state: "State", store: Store, context: "FSMGameCtxProxy"):
        if not (View := cls._resolve(state)):  # TODO testing
            logger.error(f"State {state.state_id} cannot be resolved")
            raise NotImplementedError  # TODO своя ошибка и убрать логирование здесь

        await View(store, context).execute()

    @classmethod
    def state_by_id(cls, _id: int) -> "State":
        return cls._STATE_INSTANCE[_id]
