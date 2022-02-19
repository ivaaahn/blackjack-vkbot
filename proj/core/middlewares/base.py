import typing


if typing.TYPE_CHECKING:
    from proj.store import CoreStore
    from ..context import FSMGameCtxProxy
    from ..states import State


class AbstractMiddleware:
    @classmethod
    async def exec(cls, state: "State", store: "CoreStore", context: "FSMGameCtxProxy"):
        pass
