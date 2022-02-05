import typing

if typing.TYPE_CHECKING:
    from proj.store import Store
    from ..context import FSMGameCtxProxy
    from ..states import State


class AbstractMiddleware:
    @classmethod
    async def exec(cls, state: "State", store: "Store", context: "FSMGameCtxProxy"):
        pass
