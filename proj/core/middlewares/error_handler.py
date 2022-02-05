import typing
from logging import getLogger


from .base import AbstractMiddleware
from .state_resolver import StateResolverMiddleware
from ...services.app_logger import get_logger

if typing.TYPE_CHECKING:
    from proj.store import Store
    from ..context import FSMGameCtxProxy
    from ..states import State

__all__ = ("ErrorHandlerMiddleware",)


logger = get_logger(__name__)



class ErrorHandlerMiddleware(AbstractMiddleware):
    @classmethod
    async def exec(
        cls, state: "State", store: "Store", context: "FSMGameCtxProxy"
    ):  # TODO мб абстрактный сделать
        try:
            await StateResolverMiddleware.exec(state, store, context)
        except Exception as err:
            logger.exception(
                f"ErrorHandlerMiddleware catch exception: {err}"
            )  # TODO обработать все
