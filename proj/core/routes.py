from proj.core import States
from proj.core.middlewares import StateResolverMiddleware
from proj.core.views import TriggerReceivedView


def setup_routes():
    sr = StateResolverMiddleware

    sr.add_state(States.WAITING_FOR_TRIGGER, TriggerReceivedView)

