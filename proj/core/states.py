__all__ = ("States",)


class State:
    # _id_iter = itertools.count()  # start from 0

    def __init__(self, _id: int) -> None:
        self._id = _id
        # self._handler = handler
        # self._id = next(self._id_iter)
        # StateResolver.add_state(self)

    @property
    def state_id(self) -> int:
        return self._id

    def __hash__(self) -> int:
        return self.state_id

    def __str__(self) -> str:
        return f"State #{self._id}"

    #


    # @property
    # def handler(self) -> Callable[["FSMGameCtxProxy", "GAccessors"], None]:
    #     return self._handler
    #
    # @handler.setter
    # def handler(self, value: Callable):
    #     self._handler = value
    #
    # def register(self, func: Callable):
    #     self.handler = func
    #
    #     @wraps(func)
    #     async def wrapper(*args, **kwargs):
    #         return await func(*args, **kwargs)
    #
    #     return wrapper


class States:
    WAITING_FOR_TRIGGER = State(0)
    WAITING_FOR_START_CHOICE = State(1)
    WAITING_FOR_ACTIONS_IN_LK = State(2)
    WAITING_FOR_PLAYERS_AMOUNT = State(3)
    WAITING_FOR_REGISTRATION = State(4)
    WAITING_FOR_BETS = State(5)
    WAITING_FOR_ACTION = State(6)
    WAITING_FOR_LAST_CHOICE = State(7)
