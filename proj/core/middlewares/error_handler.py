import typing


from .base import AbstractMiddleware
from .state_resolver import StateResolverMiddleware

if typing.TYPE_CHECKING:
    from proj.store import CoreStore
    from ..context import FSMGameCtxProxy
    from ..states import State

__all__ = ("ErrorHandlerMiddleware",)


class ErrorHandlerMiddleware(AbstractMiddleware):
    @classmethod
    async def exec(
        cls, state: "State", store: "CoreStore", context: "FSMGameCtxProxy"
    ):  # TODO мб абстрактный сделать
        logger = store.app.get_logger("ErrorHandlerMiddleware")

        try:
            await StateResolverMiddleware.exec(state, store, context)
        except Exception as err:
            logger.exception(
                f"ErrorHandlerMiddleware catch exception: {err}"
            )  # TODO обработать все
            raise Exception from err
